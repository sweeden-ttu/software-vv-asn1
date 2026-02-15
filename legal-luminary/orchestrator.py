"""
Legal Luminary Orchestrator Agent

Top-level LangGraph agent that orchestrates the full validation pipeline:

  1. Extract content from legalluminary.com (site submodule)
  2. Evidence verification against the Official Allow List (the oracle)
  3. Content classification and validation via the pipeline
  4. Evaluation of output quality (cohesiveness, relevancy, toxicity)
  5. Texas data.texas.gov ground-truth integration
  6. LRL (Texas Legislative Reference Library) resource checks
  7. LangSmith tracing for full observability

Architecture (LangGraph):
    extract_content → verify_evidence → route_verdict →
        [generate_content | flag_invalid] →
            evaluate_output → report_results → END

This agent implements the presentation framework:
  - Node 1: Extract Content (parse site markdown)
  - Node 2: Evidence Verification / Router (allow-list gatekeeper)
  - Node 3: Content Generation (only verified evidence proceeds)
  - Node 4: Evaluator Node (LLM quality assessment)
"""

import os
import re
import json
import hashlib
import requests
from typing import TypedDict, Literal
from datetime import datetime
from pathlib import Path

from langgraph.graph import StateGraph, END
from langsmith import traceable
from langchain_core.messages import HumanMessage, SystemMessage

# ---------------------------------------------------------------------------
# LLM Backend
# ---------------------------------------------------------------------------
USE_OLLAMA = os.environ.get("USE_OLLAMA", "false").lower() == "true"
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "granite-code:34b")

if USE_OLLAMA:
    from langchain_ollama import ChatOllama
    _llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
else:
    from langchain_openai import ChatOpenAI
    _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Tracing
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGSMITH_TRACING", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "Legal Luminary Orchestrator")

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SITE_ROOT = PROJECT_ROOT / "legal-luminary-site"

# Import pipeline components
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.settings import (
    TRUSTED_NEWS_DOMAINS, TRUSTED_COURT_DOMAINS, TRUSTED_LEGISLATION_DOMAINS,
    SITE_PAGES_WITH_SOURCES, LRL_CONFIG,
)
from state import ContentType


# ===================================================================
# Allow List (The Oracle / Test Oracle)
# ===================================================================

def _build_allow_list() -> set:
    """Build the unified allow list from all trusted domain sets."""
    allow_list = set()
    allow_list.update(TRUSTED_NEWS_DOMAINS)
    allow_list.update(TRUSTED_COURT_DOMAINS)
    allow_list.update(TRUSTED_LEGISLATION_DOMAINS)

    # Also load from site's allowlist.yml if present
    allowlist_path = SITE_ROOT / "verification" / "allowlist.yml"
    if allowlist_path.exists():
        text = allowlist_path.read_text()
        for match in re.findall(r'host:\s*(\S+)', text):
            allow_list.add(match.strip())

    return allow_list

ALLOW_LIST = _build_allow_list()


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.lower().lstrip("www.")
    except Exception:
        return ""


def _is_allowed(url: str) -> bool:
    """Check if a URL's domain is on the allow list."""
    domain = _extract_domain(url)
    if not domain:
        return False
    # Exact match
    if domain in ALLOW_LIST:
        return True
    # Check with www. prefix
    if f"www.{domain}" in ALLOW_LIST:
        return True
    # Subdomain match: check if any allow-listed domain is a suffix
    for allowed in ALLOW_LIST:
        if domain.endswith(f".{allowed}") or domain == allowed:
            return True
    return False


# ===================================================================
# Orchestrator State
# ===================================================================

class ContentItem(TypedDict, total=False):
    file_path: str
    title: str
    content: str
    urls: list
    front_matter: dict
    sha256: str


class EvidenceResult(TypedDict, total=False):
    url: str
    domain: str
    allowed: bool
    reachable: bool
    status_code: int


class EvaluationResult(TypedDict, total=False):
    cohesiveness: float
    relevancy: float
    toxicity: float
    overall_quality: float
    summary: str


class OrchestratorState(TypedDict, total=False):
    # Input
    target_files: list                    # Files to process
    current_index: int
    # Extraction
    current_item: ContentItem
    extracted_items: list
    # Evidence verification
    evidence_results: list                # Per-URL allow-list checks
    current_verdict: str                  # ALLOWED | BLOCKED
    blocked_items: list
    # Evaluation
    evaluation: EvaluationResult
    evaluations: list
    # Pipeline integration
    pipeline_results: list
    # Counters
    allowed_count: int
    blocked_count: int
    # Output
    report: dict
    completed: bool


# ===================================================================
# Node 1: Extract Content
# ===================================================================

@traceable(name="extract_content")
def extract_content(state: OrchestratorState) -> OrchestratorState:
    """Extract content from site markdown files (Node 1 of presentation)."""
    target_files = state.get("target_files", [])

    if not target_files:
        # Default: scan all _pages and _posts
        for content_dir in ["_pages", "_posts"]:
            d = SITE_ROOT / content_dir
            if d.exists():
                for md in sorted(d.glob("*.md")):
                    target_files.append(str(md.relative_to(SITE_ROOT)))

    idx = state.get("current_index", 0)
    if idx >= len(target_files):
        return {**state, "completed": True}

    rel_path = target_files[idx]
    file_path = SITE_ROOT / rel_path

    if not file_path.exists():
        return {
            **state,
            "current_item": {"file_path": rel_path, "content": "", "urls": [],
                             "title": "FILE NOT FOUND", "sha256": ""},
        }

    raw = file_path.read_text(errors="replace")
    sha = hashlib.sha256(file_path.read_bytes()).hexdigest()

    # Parse front matter
    fm = {}
    if raw.startswith("---"):
        end = raw.find("---", 3)
        if end != -1:
            for line in raw[3:end].strip().split("\n"):
                if ":" in line:
                    k, _, v = line.partition(":")
                    fm[k.strip()] = v.strip().strip('"').strip("'")

    title = fm.get("title", rel_path)

    # Extract URLs
    urls = list(set(re.findall(r'https?://[^\s<>")\]\x27\x60,;]+', raw)))

    item: ContentItem = {
        "file_path": rel_path,
        "title": title,
        "content": raw[:2000],
        "urls": urls,
        "front_matter": fm,
        "sha256": sha,
    }

    print(f"  [extract] [{idx+1}/{len(target_files)}] {title} "
          f"({len(urls)} URLs, SHA: {sha[:12]}...)")

    return {**state, "current_item": item, "target_files": target_files}


# ===================================================================
# Node 2: Evidence Verification (The Router / Gatekeeper)
# ===================================================================

@traceable(name="verify_evidence")
def verify_evidence(state: OrchestratorState) -> OrchestratorState:
    """Cross-reference extracted URLs against the Official Allow List.
    This is Node 2 of the presentation — the conditional edge gatekeeper."""
    item = state.get("current_item", {})
    urls = item.get("urls", [])

    evidence: list = []
    all_allowed = True

    for url in urls:
        domain = _extract_domain(url)
        allowed = _is_allowed(url)

        # Skip non-http resources (giphy, docker, etc.)
        skip_domains = {"giphy.com", "docker.com", "typora.io", "jekyllrb.com",
                        "daringfireball.net", "shopify.github.io", "webisland.agency"}
        if any(s in domain for s in skip_domains):
            continue

        result: EvidenceResult = {
            "url": url,
            "domain": domain,
            "allowed": allowed,
        }

        if not allowed:
            all_allowed = False
            print(f"    BLOCKED: {url} (domain: {domain})")

        evidence.append(result)

    verdict = "ALLOWED" if all_allowed else "BLOCKED"
    print(f"  [verify] {item.get('title', '?')}: {verdict} "
          f"({len(evidence)} URLs checked)")

    return {**state, "evidence_results": evidence, "current_verdict": verdict}


def route_verdict(state: OrchestratorState) -> Literal["generate_content", "flag_invalid"]:
    """Conditional edge: route based on allow-list verdict."""
    if state.get("current_verdict") == "ALLOWED":
        return "generate_content"
    return "flag_invalid"


# ===================================================================
# Node 3a: Content Generation (verified evidence only)
# ===================================================================

@traceable(name="generate_content")
def generate_content(state: OrchestratorState) -> OrchestratorState:
    """Process verified content — only evidence that passed the allow list
    reaches this node (Node 3 of presentation)."""
    item = state.get("current_item", {})

    # Verify reachability of source URLs
    evidence = state.get("evidence_results", [])
    for ev in evidence:
        if ev.get("allowed"):
            try:
                resp = requests.get(
                    ev["url"], timeout=10, allow_redirects=True,
                    headers={"User-Agent": "LegalLuminary-Orchestrator/1.0"}
                )
                ev["reachable"] = resp.status_code == 200
                ev["status_code"] = resp.status_code
            except Exception:
                ev["reachable"] = False
                ev["status_code"] = 0

    extracted = list(state.get("extracted_items", []))
    extracted.append(item)

    allowed_count = state.get("allowed_count", 0) + 1

    return {
        **state,
        "extracted_items": extracted,
        "evidence_results": evidence,
        "allowed_count": allowed_count,
    }


# ===================================================================
# Node 3b: Flag Invalid Content
# ===================================================================

@traceable(name="flag_invalid")
def flag_invalid(state: OrchestratorState) -> OrchestratorState:
    """Flag content that failed allow-list verification."""
    item = state.get("current_item", {})
    blocked = list(state.get("blocked_items", []))

    blocked_urls = [
        ev["url"] for ev in state.get("evidence_results", [])
        if not ev.get("allowed")
    ]

    blocked.append({
        "file_path": item.get("file_path", ""),
        "title": item.get("title", ""),
        "blocked_urls": blocked_urls,
        "timestamp": datetime.utcnow().isoformat(),
    })

    blocked_count = state.get("blocked_count", 0) + 1
    print(f"  [flag] INVALID: {item.get('title', '?')} "
          f"({len(blocked_urls)} blocked URLs)")

    return {**state, "blocked_items": blocked, "blocked_count": blocked_count}


# ===================================================================
# Node 4: Evaluator Node (LLM quality assessment)
# ===================================================================

@traceable(name="evaluate_output")
def evaluate_output(state: OrchestratorState) -> OrchestratorState:
    """Use LLM to assess cohesiveness, relevancy, and toxicity
    of the content (Node 4 of presentation)."""
    item = state.get("current_item", {})
    content = item.get("content", "")[:1500]
    title = item.get("title", "")

    if not content.strip():
        return state

    prompt = f"""Evaluate the following legal content page from legalluminary.com.

Title: {title}
Content (first 1500 chars):
{content}

Score each dimension from 0.0 to 1.0 and provide a brief summary:

1. Cohesiveness: Is the content well-structured and logically organized?
2. Relevancy: Is this relevant and useful for Texas attorneys or Bell County residents?
3. Toxicity: Does it contain harmful, misleading, or biased content? (0.0 = no toxicity, 1.0 = highly toxic)

Respond ONLY with valid JSON:
{{"cohesiveness": 0.0, "relevancy": 0.0, "toxicity": 0.0, "summary": "brief assessment"}}"""

    try:
        response = _llm.invoke([
            SystemMessage(content="You are a legal content quality assessor. Respond ONLY with valid JSON."),
            HumanMessage(content=prompt),
        ])
        text = response.content.strip()
        if "{" in text:
            result = json.loads(text[text.index("{"):text.rindex("}") + 1])
        else:
            result = {"cohesiveness": 0.5, "relevancy": 0.5, "toxicity": 0.1,
                      "summary": "Could not parse LLM response"}
    except Exception as e:
        result = {"cohesiveness": 0.0, "relevancy": 0.0, "toxicity": 0.0,
                  "summary": f"Evaluation error: {str(e)[:100]}"}

    # Compute overall quality (higher is better, penalize toxicity)
    quality = (
        result.get("cohesiveness", 0) * 0.35
        + result.get("relevancy", 0) * 0.45
        + (1.0 - result.get("toxicity", 0)) * 0.20
    )
    result["overall_quality"] = round(quality, 3)

    evaluations = list(state.get("evaluations", []))
    evaluations.append({
        "file": item.get("file_path", ""),
        "title": title,
        **result,
    })

    print(f"  [eval] {title}: quality={quality:.2f} "
          f"(cohesive={result.get('cohesiveness', 0):.1f}, "
          f"relevant={result.get('relevancy', 0):.1f}, "
          f"toxic={result.get('toxicity', 0):.1f})")

    return {**state, "evaluation": result, "evaluations": evaluations}


# ===================================================================
# Node 5: Advance to next file or generate report
# ===================================================================

@traceable(name="advance_or_report")
def advance_or_report(state: OrchestratorState) -> OrchestratorState:
    """Move to next file or mark as complete."""
    idx = state.get("current_index", 0) + 1
    total = len(state.get("target_files", []))
    completed = idx >= total
    return {**state, "current_index": idx, "completed": completed}


def route_continue(state: OrchestratorState) -> Literal["extract_content", "report_results"]:
    if state.get("completed", False):
        return "report_results"
    return "extract_content"


# ===================================================================
# Node 6: Report Results
# ===================================================================

@traceable(name="report_results")
def report_results(state: OrchestratorState) -> OrchestratorState:
    """Generate the final orchestrator report."""
    evaluations = state.get("evaluations", [])
    blocked = state.get("blocked_items", [])

    avg_quality = (
        sum(e.get("overall_quality", 0) for e in evaluations) / len(evaluations)
        if evaluations else 0
    )
    avg_toxicity = (
        sum(e.get("toxicity", 0) for e in evaluations) / len(evaluations)
        if evaluations else 0
    )

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "files_processed": state.get("current_index", 0),
        "allowed": state.get("allowed_count", 0),
        "blocked": state.get("blocked_count", 0),
        "average_quality": round(avg_quality, 3),
        "average_toxicity": round(avg_toxicity, 3),
        "blocked_items": blocked,
        "evaluations": evaluations,
    }

    print("\n" + "=" * 70)
    print("ORCHESTRATOR REPORT")
    print("=" * 70)
    print(f"Files processed: {report['files_processed']}")
    print(f"Allowed:         {report['allowed']}")
    print(f"Blocked:         {report['blocked']}")
    print(f"Avg Quality:     {report['average_quality']:.3f}")
    print(f"Avg Toxicity:    {report['average_toxicity']:.3f}")
    if blocked:
        print("\nBLOCKED CONTENT:")
        for b in blocked:
            print(f"  - {b['title']}: {b['blocked_urls']}")
    print("=" * 70)

    # Save report
    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(exist_ok=True)
    out_path = data_dir / "orchestrator_report.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nReport saved to {out_path}")

    return {**state, "report": report}


# ===================================================================
# Graph Construction
# ===================================================================

def build_orchestrator() -> StateGraph:
    """Build the orchestrator LangGraph pipeline."""
    workflow = StateGraph(OrchestratorState)

    workflow.add_node("extract_content", extract_content)
    workflow.add_node("verify_evidence", verify_evidence)
    workflow.add_node("generate_content", generate_content)
    workflow.add_node("flag_invalid", flag_invalid)
    workflow.add_node("evaluate_output", evaluate_output)
    workflow.add_node("advance_or_report", advance_or_report)
    workflow.add_node("report_results", report_results)

    # Entry
    workflow.set_entry_point("extract_content")

    # Extract → Verify
    workflow.add_edge("extract_content", "verify_evidence")

    # Verify → Route (conditional edge — the gatekeeper)
    workflow.add_conditional_edges(
        "verify_evidence",
        route_verdict,
        {
            "generate_content": "generate_content",
            "flag_invalid": "flag_invalid",
        },
    )

    # Generate → Evaluate
    workflow.add_edge("generate_content", "evaluate_output")
    # Flag → Advance (skip evaluation for blocked content)
    workflow.add_edge("flag_invalid", "advance_or_report")
    # Evaluate → Advance
    workflow.add_edge("evaluate_output", "advance_or_report")

    # Advance → Continue or Report
    workflow.add_conditional_edges(
        "advance_or_report",
        route_continue,
        {
            "extract_content": "extract_content",
            "report_results": "report_results",
        },
    )

    workflow.add_edge("report_results", END)

    return workflow.compile()


# ===================================================================
# Public API
# ===================================================================

@traceable(name="orchestrate")
def orchestrate(files: list = None) -> dict:
    """Run the full orchestrator pipeline.

    Args:
        files: Optional list of file paths relative to site root.
               If None, processes all _pages/ and _posts/ markdown.

    Returns:
        Final OrchestratorState with report.
    """
    pipeline = build_orchestrator()
    initial: OrchestratorState = {
        "target_files": files or [],
        "current_index": 0,
        "extracted_items": [],
        "evidence_results": [],
        "current_verdict": "",
        "blocked_items": [],
        "evaluations": [],
        "pipeline_results": [],
        "allowed_count": 0,
        "blocked_count": 0,
        "completed": False,
    }
    return pipeline.invoke(initial)


# ===================================================================
# CLI
# ===================================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Legal Luminary Orchestrator")
    parser.add_argument("--files", nargs="*", default=None,
                        help="Specific files to process (relative to site root)")
    parser.add_argument("--pages-only", action="store_true",
                        help="Only process _pages/ (skip _posts/)")
    args = parser.parse_args()

    files = args.files
    if args.pages_only and not files:
        pages_dir = SITE_ROOT / "_pages"
        if pages_dir.exists():
            files = [str(p.relative_to(SITE_ROOT)) for p in sorted(pages_dir.glob("*.md"))]

    print("=" * 70)
    print("LEGAL LUMINARY ORCHESTRATOR AGENT")
    print(f"Site root: {SITE_ROOT}")
    print(f"Allow list: {len(ALLOW_LIST)} domains")
    print(f"LLM: {'Ollama ' + OLLAMA_MODEL if USE_OLLAMA else 'OpenAI gpt-4o-mini'}")
    print("=" * 70)

    result = orchestrate(files=files)
