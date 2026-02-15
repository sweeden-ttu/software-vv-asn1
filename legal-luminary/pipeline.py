"""
Legal Luminary — Main LangGraph Validation Pipeline

This is the core pipeline that routes content through the appropriate
validator agents based on content type, with retry logic and human
escalation for failed validations.

Architecture:
    classify_content → route_to_validator → [validator_node] → aggregate_results → [retry/escalate/pass]

All nodes are traced via LangSmith.
"""

import os
import sys
from typing import Literal
from langsmith import traceable
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Project imports
sys.path.insert(0, os.path.dirname(__file__))
from state import PipelineState, create_initial_state, ContentType, VerificationStatus
from config.settings import MAX_VALIDATOR_RETRIES, MIN_CONFIDENCE_THRESHOLD
from validators.news_validator import validate_news_source
from validators.judge_validator import validate_judge
from validators.official_validator import validate_official
from validators.election_validator import validate_election
from validators.law_validator import validate_law
from validators.court_doc_validator import validate_court_document
from validators.template_validator import validate_legal_template

# Ensure tracing is enabled
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")


# ============================================================================
# Node 1: Content Classification
# ============================================================================

@traceable(name="classify_content")
def classify_content(state: PipelineState) -> PipelineState:
    """
    Classify the input content to determine which validator to route to.
    Uses LLM to detect content type from the query and raw content.
    """
    query = state.get("query", "")
    raw_content = state.get("raw_content", "")
    explicit_type = state.get("content_type", "")

    # If content type is explicitly provided, use it
    if explicit_type and explicit_type in [ct.value for ct in ContentType]:
        print(f"  [classify] Using explicit content type: {explicit_type}")
        return {
            **state,
            "detected_content_type": explicit_type,
            "classification_confidence": 1.0,
        }

    # Otherwise, use LLM to classify
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    messages = [
        SystemMessage(content=f"""Classify the following legal/governmental content into exactly ONE category.
Categories: {', '.join(ct.value for ct in ContentType)}

Respond with ONLY the category name, nothing else."""),
        HumanMessage(content=f"Query: {query}\nContent: {raw_content[:500]}")
    ]

    response = llm.invoke(messages)
    detected = response.content.strip().lower()

    # Validate against known types
    valid_types = [ct.value for ct in ContentType]
    if detected not in valid_types:
        # Try fuzzy match
        for ct in valid_types:
            if ct in detected or detected in ct:
                detected = ct
                break
        else:
            detected = ContentType.NEWS_SOURCE.value  # fallback

    print(f"  [classify] Detected content type: {detected}")
    return {
        **state,
        "detected_content_type": detected,
        "classification_confidence": 0.85,
    }


# ============================================================================
# Node 2: Router — Select Validator
# ============================================================================

def route_to_validator(state: PipelineState) -> str:
    """Route to the appropriate validator based on detected content type."""
    content_type = state.get("detected_content_type", "")
    route_map = {
        ContentType.NEWS_SOURCE.value: "validate_news",
        ContentType.JUDGE.value: "validate_judge",
        ContentType.OFFICIAL.value: "validate_official",
        ContentType.ELECTION.value: "validate_election",
        ContentType.LAW.value: "validate_law",
        ContentType.COURT_DOCUMENT.value: "validate_court_doc",
        ContentType.LEGAL_TEMPLATE.value: "validate_template",
    }
    route = route_map.get(content_type, "validate_news")
    print(f"  [route] Routing to: {route}")
    return route


# ============================================================================
# Node 3: Aggregate Results
# ============================================================================

@traceable(name="aggregate_results")
def aggregate_results(state: PipelineState) -> PipelineState:
    """
    Aggregate validation results from the chosen validator.
    Determine overall status, confidence, and whether to retry.
    """
    content_type = state.get("detected_content_type", "")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", MAX_VALIDATOR_RETRIES)

    # Find the relevant validation result
    validation_map = {
        ContentType.NEWS_SOURCE.value: state.get("news_validation", {}),
        ContentType.JUDGE.value: state.get("judge_validation", {}),
        ContentType.OFFICIAL.value: state.get("official_validation", {}),
        ContentType.ELECTION.value: state.get("election_validation", {}),
        ContentType.LAW.value: state.get("law_validation", {}),
        ContentType.COURT_DOCUMENT.value: state.get("court_doc_validation", {}),
        ContentType.LEGAL_TEMPLATE.value: state.get("template_validation", {}),
    }

    validation = validation_map.get(content_type, {})
    is_valid = validation.get("is_valid", False)
    confidence = validation.get("confidence", 0.0)

    if is_valid:
        status = VerificationStatus.VERIFIED
        should_retry = False
        escalate = False
        verified_content = state.get("query", "")
    elif retry_count < max_retries:
        status = VerificationStatus.PENDING
        should_retry = True
        escalate = False
        verified_content = ""
    else:
        status = VerificationStatus.ESCALATED
        should_retry = False
        escalate = True
        verified_content = ""

    provenance = validation.get("provenance", {})

    print(f"  [aggregate] Status: {status}, Confidence: {confidence:.3f}, "
          f"Retry: {should_retry}, Escalate: {escalate}")

    return {
        **state,
        "overall_status": status,
        "overall_confidence": confidence,
        "should_retry": should_retry,
        "escalate_to_human": escalate,
        "provenance": provenance,
        "verified_content": verified_content,
        "retry_count": retry_count + (1 if should_retry else 0),
    }


# ============================================================================
# Node 4: Retry or Finalize Router
# ============================================================================

def route_retry_or_finalize(state: PipelineState) -> Literal["classify_content", "__end__"]:
    """Decide whether to retry validation or finalize."""
    if state.get("should_retry", False):
        print(f"  [retry] Retrying (attempt {state.get('retry_count', 0)})")
        return "classify_content"
    return "__end__"


# ============================================================================
# Graph Construction
# ============================================================================

def build_pipeline() -> StateGraph:
    """Build and compile the Legal Luminary validation pipeline."""
    workflow = StateGraph(PipelineState)

    # Add nodes
    workflow.add_node("classify_content", classify_content)
    workflow.add_node("validate_news", validate_news_source)
    workflow.add_node("validate_judge", validate_judge)
    workflow.add_node("validate_official", validate_official)
    workflow.add_node("validate_election", validate_election)
    workflow.add_node("validate_law", validate_law)
    workflow.add_node("validate_court_doc", validate_court_document)
    workflow.add_node("validate_template", validate_legal_template)
    workflow.add_node("aggregate_results", aggregate_results)

    # Entry point
    workflow.set_entry_point("classify_content")

    # Conditional routing from classifier to validators
    workflow.add_conditional_edges(
        "classify_content",
        route_to_validator,
        {
            "validate_news": "validate_news",
            "validate_judge": "validate_judge",
            "validate_official": "validate_official",
            "validate_election": "validate_election",
            "validate_law": "validate_law",
            "validate_court_doc": "validate_court_doc",
            "validate_template": "validate_template",
        },
    )

    # All validators flow to aggregator
    for validator in ["validate_news", "validate_judge", "validate_official",
                      "validate_election", "validate_law", "validate_court_doc",
                      "validate_template"]:
        workflow.add_edge(validator, "aggregate_results")

    # Retry or finalize
    workflow.add_conditional_edges(
        "aggregate_results",
        route_retry_or_finalize,
        {
            "classify_content": "classify_content",
            "__end__": END,
        },
    )

    return workflow.compile()


# ============================================================================
# Public API
# ============================================================================

@traceable(name="legal_luminary_validate")
def validate(content_type: str, query: str, raw_content: str = "") -> dict:
    """
    Main entry point for the Legal Luminary validation pipeline.

    Args:
        content_type: One of ContentType values (or empty for auto-detection)
        query: The claim or content to validate
        raw_content: Optional raw LLM-generated content to verify

    Returns:
        Final PipelineState with validation results and provenance
    """
    pipeline = build_pipeline()
    initial_state = create_initial_state(content_type, query, raw_content)
    result = pipeline.invoke(initial_state)
    return result


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("LEGAL LUMINARY — Trustworthy AI Content Validator")
    print("=" * 70)

    # Demo validations across all content types
    test_cases = [
        {
            "content_type": "court_document",
            "query": "Brown v. Board of Education, 347 U.S. 483 (1954)",
            "description": "Famous Supreme Court case citation",
        },
        {
            "content_type": "judge",
            "query": "Chief Justice John Roberts, U.S. Supreme Court",
            "description": "Current Chief Justice",
        },
        {
            "content_type": "official",
            "query": "Senator Ted Cruz, Texas, Republican",
            "description": "Current U.S. Senator",
        },
        {
            "content_type": "law",
            "query": "42 U.S.C. § 1983 - Civil Rights Act",
            "description": "Federal civil rights statute",
        },
        {
            "content_type": "news_source",
            "query": "https://www.supremecourt.gov/opinions/slipopinions.aspx",
            "description": "Supreme Court official opinions page",
        },
        {
            "content_type": "election",
            "query": "2024 Presidential Election, Joe Biden vs Donald Trump",
            "description": "Recent presidential election",
        },
        {
            "content_type": "legal_template",
            "query": "Federal Court Form AO 440 - Summons in a Civil Action",
            "description": "Official federal court form",
        },
    ]

    for i, tc in enumerate(test_cases, 1):
        print(f"\n{'#' * 70}")
        print(f"# Test {i}: {tc['description']}")
        print(f"# Type: {tc['content_type']}")
        print(f"# Query: {tc['query']}")
        print(f"{'#' * 70}")

        result = validate(
            content_type=tc["content_type"],
            query=tc["query"],
        )

        print(f"\n  RESULT: {result.get('overall_status', 'unknown')}")
        print(f"  CONFIDENCE: {result.get('overall_confidence', 0):.3f}")
        print(f"  PROVENANCE: {result.get('provenance', {})}")
        print()
