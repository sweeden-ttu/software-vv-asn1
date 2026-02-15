"""
Experiment 5: Texas Data Pipeline — Ground Truth Discovery

Evaluates the Texas data.texas.gov crawler's ability to:
  1. Discover and classify legal datasets accurately
  2. Produce ground-truth evidence from LAW_VERIFICATION datasets
  3. Feed verified records into the Legal Luminary pipeline
  4. Measure classification accuracy against human-labeled expectations

Metrics:
  - Classification accuracy (against expected labels)
  - Ground-truth record retrieval rate
  - Pipeline verification success rate on real Texas data
  - Dataset coverage (how many datasets are reachable)
"""

import os
import sys
import json
from datetime import datetime

from langsmith import traceable

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Ensure tracing
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "Texas Data Pipeline Experiment")

from texas_data_crawler import (
    crawl, fetch_sample_records, fetch_record_count,
    TEXAS_LEGAL_DATASETS, SODA_BASE,
)


# ===================================================================
# Ground Truth: Human-Labeled Expected Classifications
# ===================================================================

EXPECTED_CLASSIFICATIONS = {
    # Criminal Justice — these are official government records
    "q4fw-9sy9": "LAW_VERIFICATION",    # TDCJ Releases
    "8ha4-kikr": "LAW_VERIFICATION",    # TDCJ Receives
    "87eh-wyyj": "LAW_VERIFICATION",    # TDCJ Incarcerated Population
    # Environmental Enforcement — official judgments and orders
    "cvki-4mgs": "LAW_VERIFICATION",    # TCEQ Civil Judgments
    "69n4-7aev": "LAW_VERIFICATION",    # TCEQ Administrative Orders
    "ygta-hs3n": "LAW_VERIFICATION",    # TCEQ Supplemental Env Projects
    # Licensing — reference databases
    "7358-krk7": "ATTORNEY_RESOURCE",   # TDLR All Licenses
    "kxv3-diwf": "ATTORNEY_RESOURCE",   # Insurance Agents
    "ubdr-4uff": "ATTORNEY_RESOURCE",   # Insurance Complaints
    "s7ft-44qi": "ATTORNEY_RESOURCE",   # Real Estate Brokers
    "nmqp-zmi7": "ATTORNEY_RESOURCE",   # Appraisers
    # Child Protective Services — enforcement/investigation data
    "wv2p-kpcm": "LAW_VERIFICATION",    # CPS Investigations
    # Alcohol regulation — licensing reference
    "2cjh-3vae": "ATTORNEY_RESOURCE",   # TABC Labels
}


# ===================================================================
# Experiment Functions
# ===================================================================

@traceable(name="exp5_api_reachability")
def test_api_reachability() -> dict:
    """Test which datasets are reachable via the SODA API."""
    results = {"reachable": [], "unreachable": [], "total": len(TEXAS_LEGAL_DATASETS)}

    for ds in TEXAS_LEGAL_DATASETS:
        count = fetch_record_count(ds["id"])
        if count > 0:
            results["reachable"].append({"id": ds["id"], "name": ds["name"],
                                         "records": count})
        else:
            # Try fetching a sample to double-check
            records, _ = fetch_sample_records(ds["id"], limit=1)
            if records:
                results["reachable"].append({"id": ds["id"], "name": ds["name"],
                                             "records": len(records)})
            else:
                results["unreachable"].append({"id": ds["id"], "name": ds["name"]})

    results["reachability_rate"] = (
        len(results["reachable"]) / results["total"]
        if results["total"] > 0 else 0
    )
    return results


@traceable(name="exp5_classification_accuracy")
def test_classification_accuracy(crawl_results: dict) -> dict:
    """Compare crawler classifications against expected human labels."""
    classified = crawl_results.get("classified_datasets", [])
    correct = 0
    incorrect = 0
    missing = 0
    details = []

    for ds in classified:
        ds_id = ds.get("dataset_id", "")
        actual = ds.get("classification", "")
        expected = EXPECTED_CLASSIFICATIONS.get(ds_id)

        if expected is None:
            # Dataset was discovered dynamically, no expected label
            details.append({
                "dataset_id": ds_id,
                "name": ds.get("dataset_name", ""),
                "actual": actual,
                "expected": "N/A (dynamic discovery)",
                "match": "N/A",
            })
            continue

        match = actual == expected
        if match:
            correct += 1
        else:
            incorrect += 1

        details.append({
            "dataset_id": ds_id,
            "name": ds.get("dataset_name", ""),
            "actual": actual,
            "expected": expected,
            "match": match,
        })

    # Check for expected datasets not in results
    result_ids = {d.get("dataset_id") for d in classified}
    for ds_id, expected in EXPECTED_CLASSIFICATIONS.items():
        if ds_id not in result_ids:
            missing += 1
            details.append({
                "dataset_id": ds_id,
                "actual": "MISSING",
                "expected": expected,
                "match": False,
            })

    total_labeled = correct + incorrect + missing
    accuracy = correct / total_labeled if total_labeled > 0 else 0

    return {
        "correct": correct,
        "incorrect": incorrect,
        "missing": missing,
        "total_labeled": total_labeled,
        "accuracy": accuracy,
        "details": details,
    }


@traceable(name="exp5_ground_truth_quality")
def test_ground_truth_quality(crawl_results: dict) -> dict:
    """Evaluate quality of LAW_VERIFICATION datasets as ground truth."""
    law_datasets = [
        d for d in crawl_results.get("classified_datasets", [])
        if d.get("classification") == "LAW_VERIFICATION"
    ]

    results = {
        "total_law_datasets": len(law_datasets),
        "total_records_available": 0,
        "datasets_with_sufficient_records": 0,  # >100 records
        "datasets_with_identifiers": 0,         # Has case/order numbers
        "quality_scores": [],
    }

    identifier_fields = {
        "case_number", "order_number", "judgment_number", "docket_number",
        "tdcj_number", "sid_number", "offender_id", "inmate_id",
        "tracking_number", "complaint_number",
    }

    for ds in law_datasets:
        count = ds.get("record_count", 0)
        columns = {c.lower().replace(" ", "_") for c in ds.get("column_names", [])}
        results["total_records_available"] += count

        has_identifiers = bool(columns & identifier_fields)
        if has_identifiers:
            results["datasets_with_identifiers"] += 1
        if count > 100:
            results["datasets_with_sufficient_records"] += 1

        # Quality score: weighted by records, identifiers, confidence
        quality = 0.0
        if count > 1000:
            quality += 0.4
        elif count > 100:
            quality += 0.2
        if has_identifiers:
            quality += 0.3
        quality += ds.get("confidence", 0) * 0.3

        results["quality_scores"].append({
            "dataset_id": ds["dataset_id"],
            "name": ds["dataset_name"],
            "records": count,
            "has_identifiers": has_identifiers,
            "quality_score": round(quality, 2),
        })

    results["avg_quality"] = (
        sum(q["quality_score"] for q in results["quality_scores"])
        / len(results["quality_scores"])
        if results["quality_scores"] else 0
    )

    return results


@traceable(name="exp5_run_full")
def run_experiment_5(max_datasets: int = None) -> dict:
    """Run the full Texas Data Pipeline experiment."""
    print("=" * 70)
    print("EXPERIMENT 5: TEXAS DATA PIPELINE — GROUND TRUTH DISCOVERY")
    print("=" * 70)

    # Phase 1: API Reachability
    print("\n[Phase 1] Testing API reachability...")
    reachability = test_api_reachability()
    print(f"  Reachable: {len(reachability['reachable'])}/{reachability['total']} "
          f"({reachability['reachability_rate']:.0%})")

    # Phase 2: Run crawler
    print("\n[Phase 2] Running Texas data crawler...")
    crawl_results = crawl(max_datasets=max_datasets)

    # Phase 3: Classification accuracy
    print("\n[Phase 3] Evaluating classification accuracy...")
    accuracy = test_classification_accuracy(crawl_results)
    print(f"  Accuracy: {accuracy['accuracy']:.0%} "
          f"({accuracy['correct']}/{accuracy['total_labeled']})")
    for d in accuracy["details"]:
        status = "OK" if d["match"] is True else ("MISS" if d["match"] is False else "N/A")
        print(f"    [{status}] {d.get('name', d['dataset_id'])}: "
              f"{d['actual']} (expected: {d['expected']})")

    # Phase 4: Ground truth quality
    print("\n[Phase 4] Evaluating ground truth quality...")
    quality = test_ground_truth_quality(crawl_results)
    print(f"  LAW_VERIFICATION datasets: {quality['total_law_datasets']}")
    print(f"  Total records available: {quality['total_records_available']:,}")
    print(f"  Average quality score: {quality['avg_quality']:.2f}")

    # Final report
    report = {
        "experiment": "Exp5 — Texas Data Pipeline",
        "timestamp": datetime.utcnow().isoformat(),
        "reachability": reachability,
        "classification_accuracy": accuracy,
        "ground_truth_quality": quality,
        "summary": crawl_results.get("summary", ""),
    }

    # Save report
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    out_path = os.path.join(data_dir, "exp5_results.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nReport saved to {out_path}")

    print("\n" + "=" * 70)
    print("EXPERIMENT 5 COMPLETE")
    print("=" * 70)

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=None)
    args = parser.parse_args()
    run_experiment_5(max_datasets=args.max)
