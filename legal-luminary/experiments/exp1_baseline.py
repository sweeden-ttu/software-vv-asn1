"""
Experiment 1: Baseline Hallucination Rate

Measures the hallucination rate of a general-purpose LLM on legal citation tasks
WITHOUT the verification pipeline. This establishes the baseline.
"""

import json
from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Ground-truth legal citations for testing
GROUND_TRUTH_CITATIONS = [
    {
        "question": "What is the case citation for the Supreme Court ruling on school desegregation in 1954?",
        "correct_citation": "Brown v. Board of Education, 347 U.S. 483 (1954)",
        "correct_year": "1954",
        "correct_court": "Supreme Court",
    },
    {
        "question": "What is the citation for the Miranda rights ruling?",
        "correct_citation": "Miranda v. Arizona, 384 U.S. 436 (1966)",
        "correct_year": "1966",
        "correct_court": "Supreme Court",
    },
    {
        "question": "What case established judicial review in the United States?",
        "correct_citation": "Marbury v. Madison, 5 U.S. (1 Cranch) 137 (1803)",
        "correct_year": "1803",
        "correct_court": "Supreme Court",
    },
    {
        "question": "What is the citation for the Roe v. Wade abortion ruling?",
        "correct_citation": "Roe v. Wade, 410 U.S. 113 (1973)",
        "correct_year": "1973",
        "correct_court": "Supreme Court",
    },
    {
        "question": "What case established the separate but equal doctrine?",
        "correct_citation": "Plessy v. Ferguson, 163 U.S. 537 (1896)",
        "correct_year": "1896",
        "correct_court": "Supreme Court",
    },
    {
        "question": "What federal statute protects civil rights and allows lawsuits against officials?",
        "correct_citation": "42 U.S.C. § 1983",
        "correct_year": "1871",
        "correct_court": "Federal Statute",
    },
    {
        "question": "What is the citation for the Citizens United campaign finance case?",
        "correct_citation": "Citizens United v. Federal Election Commission, 558 U.S. 310 (2010)",
        "correct_year": "2010",
        "correct_court": "Supreme Court",
    },
    {
        "question": "What landmark case addressed the right to counsel for indigent defendants?",
        "correct_citation": "Gideon v. Wainwright, 372 U.S. 335 (1963)",
        "correct_year": "1963",
        "correct_court": "Supreme Court",
    },
    {
        "question": "What case ruled on the constitutionality of the Affordable Care Act?",
        "correct_citation": "National Federation of Independent Business v. Sebelius, 567 U.S. 519 (2012)",
        "correct_year": "2012",
        "correct_court": "Supreme Court",
    },
    {
        "question": "What is the citation for the Loving v. Virginia interracial marriage case?",
        "correct_citation": "Loving v. Virginia, 388 U.S. 1 (1967)",
        "correct_year": "1967",
        "correct_court": "Supreme Court",
    },
]


@traceable(name="exp1_ask_llm_citation")
def ask_llm_citation(question: str) -> str:
    """Ask LLM to provide a legal citation without verification."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    messages = [
        SystemMessage(content="You are a legal assistant. Provide the exact legal citation "
                      "for the following question. Include case name, volume, reporter, page, "
                      "and year. Be specific and precise."),
        HumanMessage(content=question),
    ]
    response = llm.invoke(messages)
    return response.content.strip()


@traceable(name="exp1_check_citation")
def check_citation(llm_response: str, ground_truth: dict) -> dict:
    """Check LLM citation against ground truth."""
    correct_citation = ground_truth["correct_citation"]
    correct_year = ground_truth["correct_year"]

    # Check if key elements are present
    has_case_name = any(
        part.lower() in llm_response.lower()
        for part in correct_citation.split(",")[0].split(" v. ")
    )
    has_year = correct_year in llm_response
    has_volume = any(
        num in llm_response
        for num in [n for n in correct_citation.split() if n.isdigit()]
    )

    is_correct = has_case_name and has_year
    is_hallucinated = not has_case_name or not has_year

    return {
        "question": ground_truth["question"],
        "llm_response": llm_response,
        "correct_citation": correct_citation,
        "has_case_name": has_case_name,
        "has_year": has_year,
        "has_volume": has_volume,
        "is_correct": is_correct,
        "is_hallucinated": is_hallucinated,
    }


@traceable(name="exp1_baseline_hallucination_rate")
def run_experiment_1() -> dict:
    """Run Experiment 1: Baseline Hallucination Rate."""
    print("=" * 70)
    print("EXPERIMENT 1: Baseline Hallucination Rate")
    print("=" * 70)

    results = []
    for gt in GROUND_TRUTH_CITATIONS:
        print(f"\n  Q: {gt['question']}")
        llm_response = ask_llm_citation(gt["question"])
        print(f"  A: {llm_response[:100]}...")
        check = check_citation(llm_response, gt)
        results.append(check)
        status = "CORRECT" if check["is_correct"] else "HALLUCINATED"
        print(f"  → {status}")

    # Calculate metrics
    total = len(results)
    correct = sum(1 for r in results if r["is_correct"])
    hallucinated = sum(1 for r in results if r["is_hallucinated"])

    metrics = {
        "total_questions": total,
        "correct": correct,
        "hallucinated": hallucinated,
        "accuracy": correct / total if total > 0 else 0,
        "hallucination_rate": hallucinated / total if total > 0 else 0,
    }

    print(f"\n{'=' * 70}")
    print(f"RESULTS:")
    print(f"  Total questions: {metrics['total_questions']}")
    print(f"  Correct: {metrics['correct']}")
    print(f"  Hallucinated: {metrics['hallucinated']}")
    print(f"  Accuracy: {metrics['accuracy']:.1%}")
    print(f"  Hallucination rate: {metrics['hallucination_rate']:.1%}")
    print(f"{'=' * 70}")

    return {"metrics": metrics, "results": results}


if __name__ == "__main__":
    run_experiment_1()
