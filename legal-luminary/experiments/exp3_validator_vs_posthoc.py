"""
Experiment 3: Validator Node vs Post-Hoc Verification

Compares two architectures:
  (A) LangGraph with validator nodes that reject and retry on failure
  (B) Simple RAG pipeline with post-hoc verification that filters outputs
Measures end-to-end accuracy and latency.
"""

import time
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pipeline import validate
from experiments.exp1_baseline import GROUND_TRUTH_CITATIONS, ask_llm_citation


@traceable(name="exp3_approach_a_langgraph")
def approach_a_langgraph(question: str) -> dict:
    """Approach A: LangGraph pipeline with retry logic."""
    start = time.time()
    llm_response = ask_llm_citation(question)
    result = validate(content_type="court_document", query=llm_response)
    elapsed = time.time() - start
    return {
        "response": llm_response,
        "verified": result.get("overall_status") == "verified",
        "confidence": result.get("overall_confidence", 0),
        "latency_seconds": elapsed,
        "retries": result.get("retry_count", 0),
    }


@traceable(name="exp3_approach_b_posthoc")
def approach_b_posthoc(question: str) -> dict:
    """Approach B: Simple LLM + post-hoc filter (no retry)."""
    start = time.time()
    llm_response = ask_llm_citation(question)

    # Post-hoc: just ask the LLM to verify its own output
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    verify_msg = [
        SystemMessage(content="You are a legal citation checker. Verify if the following "
                      "citation is real and accurate. Respond with VERIFIED or UNVERIFIED."),
        HumanMessage(content=llm_response),
    ]
    verify_response = llm.invoke(verify_msg)
    verified = "VERIFIED" in verify_response.content.upper()

    elapsed = time.time() - start
    return {
        "response": llm_response,
        "verified": verified,
        "confidence": 0.5 if verified else 0.2,
        "latency_seconds": elapsed,
        "retries": 0,
    }


@traceable(name="exp3_validator_vs_posthoc")
def run_experiment_3() -> dict:
    """Run Experiment 3: Compare architectures."""
    print("=" * 70)
    print("EXPERIMENT 3: Validator Node vs Post-Hoc Verification")
    print("=" * 70)

    results_a, results_b = [], []

    for gt in GROUND_TRUTH_CITATIONS[:5]:  # Use subset for speed
        print(f"\n  Q: {gt['question']}")

        a = approach_a_langgraph(gt["question"])
        print(f"  [A] LangGraph: {'VERIFIED' if a['verified'] else 'REJECTED'} "
              f"({a['latency_seconds']:.1f}s, {a['retries']} retries)")
        results_a.append(a)

        b = approach_b_posthoc(gt["question"])
        print(f"  [B] Post-hoc:  {'VERIFIED' if b['verified'] else 'REJECTED'} "
              f"({b['latency_seconds']:.1f}s)")
        results_b.append(b)

    # Metrics
    avg_latency_a = sum(r["latency_seconds"] for r in results_a) / len(results_a)
    avg_latency_b = sum(r["latency_seconds"] for r in results_b) / len(results_b)
    verified_a = sum(1 for r in results_a if r["verified"])
    verified_b = sum(1 for r in results_b if r["verified"])

    metrics = {
        "approach_a_langgraph": {
            "verified_count": verified_a,
            "avg_latency": round(avg_latency_a, 2),
            "avg_confidence": round(sum(r["confidence"] for r in results_a) / len(results_a), 3),
        },
        "approach_b_posthoc": {
            "verified_count": verified_b,
            "avg_latency": round(avg_latency_b, 2),
            "avg_confidence": round(sum(r["confidence"] for r in results_b) / len(results_b), 3),
        },
    }

    print(f"\n{'=' * 70}")
    print(f"COMPARISON:")
    print(f"  [A] LangGraph: {verified_a} verified, {avg_latency_a:.1f}s avg latency")
    print(f"  [B] Post-hoc:  {verified_b} verified, {avg_latency_b:.1f}s avg latency")
    print(f"{'=' * 70}")

    return {"metrics": metrics}


if __name__ == "__main__":
    run_experiment_3()
