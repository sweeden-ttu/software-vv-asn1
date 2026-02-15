"""
Experiment 2: Verification Pipeline Effectiveness

Runs the same legal citation tasks through the LLM, then passes outputs
through the Legal Luminary validator pipeline. Measures precision, recall,
and hallucination rate with the pipeline active.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pipeline import validate
from experiments.exp1_baseline import GROUND_TRUTH_CITATIONS, ask_llm_citation


@traceable(name="exp2_validate_citation")
def validate_citation_with_pipeline(llm_response: str, ground_truth: dict) -> dict:
    """Validate an LLM-generated citation through the pipeline."""
    # Run through the validator pipeline
    result = validate(
        content_type="court_document",
        query=llm_response,
        raw_content=f"Question: {ground_truth['question']}\nCitation: {llm_response}",
    )

    pipeline_verified = result.get("overall_status") == "verified"
    pipeline_confidence = result.get("overall_confidence", 0)

    # Check against ground truth
    correct_citation = ground_truth["correct_citation"]
    has_case_name = any(
        part.lower() in llm_response.lower()
        for part in correct_citation.split(",")[0].split(" v. ")
    )
    has_year = ground_truth["correct_year"] in llm_response
    actually_correct = has_case_name and has_year

    return {
        "question": ground_truth["question"],
        "llm_response": llm_response,
        "pipeline_verified": pipeline_verified,
        "pipeline_confidence": pipeline_confidence,
        "actually_correct": actually_correct,
        "true_positive": pipeline_verified and actually_correct,
        "false_positive": pipeline_verified and not actually_correct,
        "true_negative": not pipeline_verified and not actually_correct,
        "false_negative": not pipeline_verified and actually_correct,
    }


@traceable(name="exp2_pipeline_effectiveness")
def run_experiment_2() -> dict:
    """Run Experiment 2: Verification Pipeline Effectiveness."""
    print("=" * 70)
    print("EXPERIMENT 2: Verification Pipeline Effectiveness")
    print("=" * 70)

    results = []
    for gt in GROUND_TRUTH_CITATIONS:
        print(f"\n  Q: {gt['question']}")
        llm_response = ask_llm_citation(gt["question"])
        print(f"  LLM: {llm_response[:80]}...")
        check = validate_citation_with_pipeline(llm_response, gt)
        results.append(check)
        print(f"  Pipeline: {'VERIFIED' if check['pipeline_verified'] else 'REJECTED'} "
              f"(conf: {check['pipeline_confidence']:.3f})")
        print(f"  Actually correct: {check['actually_correct']}")

    # Calculate precision, recall, hallucination rate
    tp = sum(1 for r in results if r["true_positive"])
    fp = sum(1 for r in results if r["false_positive"])
    tn = sum(1 for r in results if r["true_negative"])
    fn = sum(1 for r in results if r["false_negative"])
    total = len(results)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    hallucination_rate = fp / total if total > 0 else 0

    metrics = {
        "total_questions": total,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "hallucination_rate_with_pipeline": hallucination_rate,
    }

    print(f"\n{'=' * 70}")
    print(f"RESULTS:")
    print(f"  Total: {total}")
    print(f"  TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}")
    print(f"  Precision: {precision:.1%}")
    print(f"  Recall: {recall:.1%}")
    print(f"  Hallucination rate (with pipeline): {hallucination_rate:.1%}")
    print(f"{'=' * 70}")

    return {"metrics": metrics, "results": results}


if __name__ == "__main__":
    run_experiment_2()
