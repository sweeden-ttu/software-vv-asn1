"""
Texas Legal Data Crawler — LangGraph Pipeline

Crawls data.texas.gov via the Socrata SODA API to discover and classify
datasets useful for Texas attorneys. Content is categorized as:

  - LAW_VERIFICATION: Data usable as ground-truth evidence
    (e.g., TDCJ incarceration records, civil judgments, administrative orders)
  - NEWS: Timely updates relevant to legal practice
  - ATTORNEY_RESOURCE: Reference data useful for daily practice
    (e.g., licensing databases, enforcement actions, regulatory filings)

The crawler feeds discovered datasets into the Legal Luminary validation
pipeline and traces every step via LangSmith.

Architecture (LangGraph):
    discover_datasets → classify_dataset → route_classification →
        [verify_law_data | tag_news | tag_resource] →
            enrich_metadata → aggregate_results → END
"""

import os
import json
import requests
from typing import TypedDict, Literal, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langsmith import traceable

# ---------------------------------------------------------------------------
# LLM Backend: Ollama (granite-code:34b on HPCC) or OpenAI fallback
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "granite-code:34b")
USE_OLLAMA = os.environ.get("USE_OLLAMA", "true").lower() == "true"

if USE_OLLAMA:
    from langchain_ollama import ChatOllama
    _llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
else:
    from langchain_openai import ChatOpenAI
    _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

from langchain_core.messages import HumanMessage, SystemMessage

# Ensure tracing
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGSMITH_TRACING", "true")


# ===================================================================
# Texas data.texas.gov — Known Legal / Attorney-Relevant Datasets
# ===================================================================

TEXAS_LEGAL_DATASETS = [
    # Criminal Justice — TDCJ
    {"id": "q4fw-9sy9", "name": "TDCJ Releases FY 2025",
     "agency": "TX Dept of Criminal Justice", "category": "Public Safety",
     "description": "All inmate releases from TDCJ for FY 2025"},
    {"id": "8ha4-kikr", "name": "TDCJ Receives FY 2025",
     "agency": "TX Dept of Criminal Justice", "category": "Public Safety",
     "description": "All inmate receives into TDCJ for FY 2025"},
    {"id": "87eh-wyyj", "name": "TDCJ Incarcerated Population Dec 2025",
     "agency": "TX Dept of Criminal Justice", "category": "Public Safety",
     "description": "Currently incarcerated inmate population with demographics, offense, and parole info"},
    # Environmental Enforcement
    {"id": "cvki-4mgs", "name": "TCEQ Civil Judgments FY 2025",
     "agency": "TX Commission on Environmental Quality", "category": "Environment",
     "description": "Civil judgments issued by TCEQ in fiscal year 2025"},
    {"id": "69n4-7aev", "name": "TCEQ Administrative Orders FY 2025",
     "agency": "TX Commission on Environmental Quality", "category": "Environment",
     "description": "Administrative orders issued by TCEQ in fiscal year 2025"},
    {"id": "ygta-hs3n", "name": "TCEQ Supplemental Environmental Projects FY 2025",
     "agency": "TX Commission on Environmental Quality", "category": "Environment",
     "description": "Supplemental environmental projects agreed to in FY 2025"},
    # Licensing & Regulatory
    {"id": "7358-krk7", "name": "TDLR All Licenses",
     "agency": "TX Dept of Licensing and Regulation", "category": "Licensing",
     "description": "Comprehensive listing of all TDLR license holders"},
    {"id": "kxv3-diwf", "name": "Insurance Agents & Adjusters",
     "agency": "TX Dept of Insurance", "category": "Licensing",
     "description": "Licensed insurance agents, adjusters, and approved managers"},
    {"id": "ubdr-4uff", "name": "Insurance Complaints All Data",
     "agency": "TX Dept of Insurance", "category": "Licensing",
     "description": "Complaints against insurance professionals, carriers, and orgs"},
    {"id": "s7ft-44qi", "name": "Broker and Sales Agent License Holders",
     "agency": "TX Real Estate Commission", "category": "Licensing",
     "description": "Broker and sales agent license holder information"},
    {"id": "nmqp-zmi7", "name": "Appraiser File",
     "agency": "TX Real Estate Commission", "category": "Licensing",
     "description": "Licensed appraiser file, updated daily"},
    # Child Protective Services
    {"id": "wv2p-kpcm", "name": "CPS Abuse/Neglect Investigations FY2016-FY2025",
     "agency": "TX Dept of Family and Protective Services", "category": "Social Services",
     "description": "Abuse/neglect investigation counts and dispositions by county"},
    # Alcohol regulation
    {"id": "2cjh-3vae", "name": "TABC Approved Product Labels",
     "agency": "TX Alcoholic Beverage Commission", "category": "Licensing",
     "description": "Product labels approved by TABC before September 1, 2021"},
]


# ===================================================================
# Pipeline State
# ===================================================================

class DatasetClassification(TypedDict, total=False):
    dataset_id: str
    dataset_name: str
    agency: str
    category: str
    description: str
    classification: str       # LAW_VERIFICATION | NEWS | ATTORNEY_RESOURCE
    confidence: float
    sample_records: list
    record_count: int
    column_names: list
    usefulness_summary: str
    ground_truth_potential: str
    api_endpoint: str
    crawl_timestamp: str
    error: str


class CrawlerState(TypedDict, total=False):
    # Input
    datasets_to_crawl: list              # List of dataset dicts
    current_index: int
    # Accumulation
    classified_datasets: list            # List of DatasetClassification
    current_dataset: dict                # Dataset being processed
    current_classification: DatasetClassification
    # Counters
    law_verification_count: int
    news_count: int
    resource_count: int
    error_count: int
    # Output
    summary: str
    completed: bool


# ===================================================================
# Socrata SODA API Helpers
# ===================================================================

SODA_BASE = "https://data.texas.gov/resource"
APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN", "")


def fetch_dataset_metadata(dataset_id: str) -> dict:
    """Fetch dataset metadata from Socrata."""
    url = f"https://data.texas.gov/api/views/{dataset_id}.json"
    headers = {}
    if APP_TOKEN:
        headers["X-App-Token"] = APP_TOKEN
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        return {"error": str(e)}
    return {"error": f"HTTP {resp.status_code}"}


def fetch_sample_records(dataset_id: str, limit: int = 5) -> tuple:
    """Fetch sample records and column info from a dataset."""
    url = f"{SODA_BASE}/{dataset_id}.json?$limit={limit}"
    headers = {}
    if APP_TOKEN:
        headers["X-App-Token"] = APP_TOKEN
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            records = resp.json()
            columns = list(records[0].keys()) if records else []
            return records, columns
    except Exception as e:
        return [], []
    return [], []


def fetch_record_count(dataset_id: str) -> int:
    """Get total record count for a dataset."""
    url = f"{SODA_BASE}/{dataset_id}.json?$select=count(*)"
    headers = {}
    if APP_TOKEN:
        headers["X-App-Token"] = APP_TOKEN
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return int(data[0].get("count", 0))
    except Exception:
        pass
    return 0


# ===================================================================
# LangGraph Nodes
# ===================================================================

@traceable(name="discover_datasets")
def discover_datasets(state: CrawlerState) -> CrawlerState:
    """Seed the crawler with known Texas legal datasets and probe the API
    for any additional datasets via search."""
    datasets = list(TEXAS_LEGAL_DATASETS)

    # Try to discover more via Socrata catalog search
    search_terms = ["court", "criminal", "attorney", "enforcement", "violation"]
    for term in search_terms:
        try:
            url = (
                f"https://api.us.socrata.com/api/catalog/v1"
                f"?domains=data.texas.gov&search_context=data.texas.gov"
                f"&q={term}&limit=5"
            )
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                known_ids = {d["id"] for d in datasets}
                for r in results:
                    res = r.get("resource", {})
                    rid = res.get("id", "")
                    if rid and rid not in known_ids:
                        datasets.append({
                            "id": rid,
                            "name": res.get("name", "Unknown"),
                            "agency": res.get("attribution", "Unknown"),
                            "category": (r.get("classification", {})
                                          .get("domain_category", "Uncategorized")),
                            "description": res.get("description", "")[:300],
                        })
                        known_ids.add(rid)
        except Exception:
            continue

    print(f"  [discover] Found {len(datasets)} datasets to crawl")
    return {
        **state,
        "datasets_to_crawl": datasets,
        "current_index": 0,
        "classified_datasets": [],
        "law_verification_count": 0,
        "news_count": 0,
        "resource_count": 0,
        "error_count": 0,
        "completed": False,
    }


@traceable(name="fetch_and_sample")
def fetch_and_sample(state: CrawlerState) -> CrawlerState:
    """Fetch sample records and metadata for the current dataset."""
    idx = state.get("current_index", 0)
    datasets = state.get("datasets_to_crawl", [])

    if idx >= len(datasets):
        return {**state, "completed": True}

    ds = datasets[idx]
    dataset_id = ds["id"]
    print(f"  [fetch] [{idx+1}/{len(datasets)}] {ds['name']} ({dataset_id})")

    records, columns = fetch_sample_records(dataset_id, limit=5)
    count = fetch_record_count(dataset_id)

    classification: DatasetClassification = {
        "dataset_id": dataset_id,
        "dataset_name": ds["name"],
        "agency": ds.get("agency", "Unknown"),
        "category": ds.get("category", ""),
        "description": ds.get("description", ""),
        "sample_records": records[:3],
        "record_count": count,
        "column_names": columns,
        "api_endpoint": f"{SODA_BASE}/{dataset_id}.json",
        "crawl_timestamp": datetime.utcnow().isoformat(),
    }

    return {**state, "current_dataset": ds, "current_classification": classification}


@traceable(name="classify_dataset")
def classify_dataset(state: CrawlerState) -> CrawlerState:
    """Use Ollama/LLM to classify the dataset."""
    c = state.get("current_classification", {})
    if not c or not c.get("dataset_id"):
        return state

    sample_str = json.dumps(c.get("sample_records", [])[:2], indent=2, default=str)[:800]
    columns_str = ", ".join(c.get("column_names", [])[:20])

    prompt = f"""You are a legal data analyst classifying Texas government datasets for attorneys.

Dataset: {c.get('dataset_name', '')}
Agency: {c.get('agency', '')}
Category: {c.get('category', '')}
Description: {c.get('description', '')}
Columns: {columns_str}
Record Count: {c.get('record_count', 0)}
Sample Records:
{sample_str}

Classify this dataset into EXACTLY ONE category:
- LAW_VERIFICATION: Official government records that can serve as ground-truth evidence in legal proceedings (criminal records, court judgments, administrative orders, enforcement actions)
- NEWS: Data that represents timely developments, new filings, or recent changes attorneys should track
- ATTORNEY_RESOURCE: Reference data useful for daily legal practice (licensing databases, regulatory filings, contact directories)

Respond in this exact JSON format:
{{"classification": "LAW_VERIFICATION or NEWS or ATTORNEY_RESOURCE", "confidence": 0.0 to 1.0, "usefulness_summary": "one sentence on why this is useful for attorneys", "ground_truth_potential": "how this can serve as evidence or ground truth in tests"}}"""

    try:
        response = _llm.invoke([
            SystemMessage(content="You are a legal data classification expert. Respond ONLY with valid JSON."),
            HumanMessage(content=prompt),
        ])
        text = response.content.strip()
        # Extract JSON from response
        if "{" in text:
            json_str = text[text.index("{"):text.rindex("}") + 1]
            result = json.loads(json_str)
        else:
            result = {"classification": "ATTORNEY_RESOURCE", "confidence": 0.5,
                      "usefulness_summary": "Could not parse LLM response",
                      "ground_truth_potential": "Unknown"}
    except Exception as e:
        result = {"classification": "ATTORNEY_RESOURCE", "confidence": 0.3,
                  "usefulness_summary": f"Classification error: {str(e)[:100]}",
                  "ground_truth_potential": "Error during classification"}

    c["classification"] = result.get("classification", "ATTORNEY_RESOURCE")
    c["confidence"] = result.get("confidence", 0.5)
    c["usefulness_summary"] = result.get("usefulness_summary", "")
    c["ground_truth_potential"] = result.get("ground_truth_potential", "")

    print(f"  [classify] {c['dataset_name']} → {c['classification']} "
          f"(confidence: {c['confidence']:.2f})")

    return {**state, "current_classification": c}


@traceable(name="validate_with_pipeline")
def validate_with_pipeline(state: CrawlerState) -> CrawlerState:
    """For LAW_VERIFICATION datasets, run a sample through the Legal Luminary
    validation pipeline to check if it produces verifiable ground truth."""
    c = state.get("current_classification", {})
    if c.get("classification") != "LAW_VERIFICATION":
        return state

    # Build a test query from the dataset
    sample = c.get("sample_records", [{}])[0] if c.get("sample_records") else {}
    if not sample:
        return state

    # Try to construct a meaningful validation query
    query_parts = []
    for key in ["name", "offender_name", "respondent", "defendant",
                "case_number", "order_number", "judgment_number"]:
        if key in sample:
            query_parts.append(f"{key}: {sample[key]}")
    if not query_parts:
        # Use first few fields
        for k, v in list(sample.items())[:3]:
            query_parts.append(f"{k}: {v}")

    test_query = "; ".join(query_parts)

    try:
        from pipeline import validate
        result = validate(
            content_type="",
            query=test_query,
            raw_content=json.dumps(sample, default=str)[:500],
        )
        c["ground_truth_potential"] = (
            f"Pipeline validation: status={result.get('overall_status', 'unknown')}, "
            f"confidence={result.get('overall_confidence', 0):.2f}. "
            f"{c.get('ground_truth_potential', '')}"
        )
    except Exception as e:
        c["ground_truth_potential"] = (
            f"Pipeline test error: {str(e)[:100]}. {c.get('ground_truth_potential', '')}"
        )

    return {**state, "current_classification": c}


@traceable(name="accumulate_result")
def accumulate_result(state: CrawlerState) -> CrawlerState:
    """Add the current classification to results and advance the index."""
    c = state.get("current_classification", {})
    classified = list(state.get("classified_datasets", []))
    classified.append(c)

    law_count = state.get("law_verification_count", 0)
    news_count = state.get("news_count", 0)
    res_count = state.get("resource_count", 0)
    err_count = state.get("error_count", 0)

    cls = c.get("classification", "")
    if cls == "LAW_VERIFICATION":
        law_count += 1
    elif cls == "NEWS":
        news_count += 1
    elif cls == "ATTORNEY_RESOURCE":
        res_count += 1
    if c.get("error"):
        err_count += 1

    next_idx = state.get("current_index", 0) + 1
    completed = next_idx >= len(state.get("datasets_to_crawl", []))

    return {
        **state,
        "classified_datasets": classified,
        "current_index": next_idx,
        "law_verification_count": law_count,
        "news_count": news_count,
        "resource_count": res_count,
        "error_count": err_count,
        "completed": completed,
    }


def route_continue_or_done(state: CrawlerState) -> Literal["fetch_and_sample", "generate_summary"]:
    """Continue crawling or generate final summary."""
    if state.get("completed", False):
        return "generate_summary"
    return "fetch_and_sample"


@traceable(name="generate_summary")
def generate_summary(state: CrawlerState) -> CrawlerState:
    """Generate a final summary of the crawl."""
    classified = state.get("classified_datasets", [])
    law_ds = [d for d in classified if d.get("classification") == "LAW_VERIFICATION"]
    news_ds = [d for d in classified if d.get("classification") == "NEWS"]
    res_ds = [d for d in classified if d.get("classification") == "ATTORNEY_RESOURCE"]

    summary_lines = [
        "=" * 70,
        "TEXAS LEGAL DATA CRAWLER — RESULTS SUMMARY",
        f"Crawled: {len(classified)} datasets from data.texas.gov",
        f"Timestamp: {datetime.utcnow().isoformat()}",
        "=" * 70,
        "",
        f"LAW VERIFICATION (ground truth): {len(law_ds)} datasets",
    ]
    for d in law_ds:
        summary_lines.append(
            f"  - {d['dataset_name']} [{d['dataset_id']}] "
            f"({d.get('record_count', 0):,} records, confidence: {d.get('confidence', 0):.2f})"
        )
        summary_lines.append(f"    {d.get('usefulness_summary', '')}")

    summary_lines.append(f"\nNEWS / TIMELY UPDATES: {len(news_ds)} datasets")
    for d in news_ds:
        summary_lines.append(
            f"  - {d['dataset_name']} [{d['dataset_id']}] "
            f"({d.get('record_count', 0):,} records)"
        )

    summary_lines.append(f"\nATTORNEY RESOURCES: {len(res_ds)} datasets")
    for d in res_ds:
        summary_lines.append(
            f"  - {d['dataset_name']} [{d['dataset_id']}] "
            f"({d.get('record_count', 0):,} records)"
        )

    summary_lines.append(f"\nErrors: {state.get('error_count', 0)}")
    summary_lines.append("=" * 70)

    summary = "\n".join(summary_lines)
    print(summary)

    return {**state, "summary": summary}


# ===================================================================
# Graph Construction
# ===================================================================

def build_crawler_pipeline() -> StateGraph:
    """Build the Texas legal data crawler LangGraph pipeline."""
    workflow = StateGraph(CrawlerState)

    workflow.add_node("discover_datasets", discover_datasets)
    workflow.add_node("fetch_and_sample", fetch_and_sample)
    workflow.add_node("classify_dataset", classify_dataset)
    workflow.add_node("validate_with_pipeline", validate_with_pipeline)
    workflow.add_node("accumulate_result", accumulate_result)
    workflow.add_node("generate_summary", generate_summary)

    workflow.set_entry_point("discover_datasets")

    workflow.add_edge("discover_datasets", "fetch_and_sample")
    workflow.add_edge("fetch_and_sample", "classify_dataset")
    workflow.add_edge("classify_dataset", "validate_with_pipeline")
    workflow.add_edge("validate_with_pipeline", "accumulate_result")

    workflow.add_conditional_edges(
        "accumulate_result",
        route_continue_or_done,
        {
            "fetch_and_sample": "fetch_and_sample",
            "generate_summary": "generate_summary",
        },
    )

    workflow.add_edge("generate_summary", END)

    return workflow.compile()


# ===================================================================
# Public API
# ===================================================================

@traceable(name="texas_data_crawl")
def crawl(max_datasets: Optional[int] = None) -> dict:
    """Run the Texas legal data crawler.

    Args:
        max_datasets: Limit the number of datasets to crawl (None = all)

    Returns:
        Final CrawlerState with all classified datasets
    """
    pipeline = build_crawler_pipeline()
    initial: CrawlerState = {
        "datasets_to_crawl": [],
        "current_index": 0,
        "classified_datasets": [],
        "law_verification_count": 0,
        "news_count": 0,
        "resource_count": 0,
        "error_count": 0,
        "completed": False,
        "summary": "",
    }

    result = pipeline.invoke(initial)

    # Save results to data/
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    out_path = os.path.join(data_dir, "texas_crawl_results.json")
    with open(out_path, "w") as f:
        # Convert to serializable form
        serializable = {
            "crawl_timestamp": datetime.utcnow().isoformat(),
            "total_datasets": len(result.get("classified_datasets", [])),
            "law_verification_count": result.get("law_verification_count", 0),
            "news_count": result.get("news_count", 0),
            "resource_count": result.get("resource_count", 0),
            "error_count": result.get("error_count", 0),
            "datasets": result.get("classified_datasets", []),
            "summary": result.get("summary", ""),
        }
        json.dump(serializable, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")

    return result


# ===================================================================
# CLI
# ===================================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Texas Legal Data Crawler")
    parser.add_argument("--max", type=int, default=None,
                        help="Max datasets to crawl")
    parser.add_argument("--ollama-url", type=str, default=None,
                        help="Ollama base URL")
    parser.add_argument("--model", type=str, default=None,
                        help="Ollama model name")
    args = parser.parse_args()

    if args.ollama_url:
        os.environ["OLLAMA_BASE_URL"] = args.ollama_url
    if args.model:
        os.environ["OLLAMA_MODEL"] = args.model

    print("=" * 70)
    print("TEXAS LEGAL DATA CRAWLER")
    print(f"LLM Backend: {'Ollama' if USE_OLLAMA else 'OpenAI'}")
    if USE_OLLAMA:
        print(f"Ollama URL: {OLLAMA_BASE_URL}")
        print(f"Model: {OLLAMA_MODEL}")
    print("=" * 70)

    result = crawl(max_datasets=args.max)
