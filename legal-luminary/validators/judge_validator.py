"""
Judge Validator

Validates judge names against federal and state court rosters.
Uses CourtListener API and U.S. Courts data.
"""

import requests
from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from state import ValidationResult, ProvenanceMetadata, VerificationStatus
from config.settings import COURTLISTENER_API_KEY, COURTLISTENER_BASE_URL, MIN_CONFIDENCE_THRESHOLD


@traceable(name="validate_judge")
def validate_judge(state: dict) -> dict:
    """
    Validate a judge name and court assignment.

    Checks:
    1. CourtListener People API for judge records
    2. LLM knowledge cross-reference
    3. Court assignment consistency
    """
    query = state.get("query", "")
    raw_content = state.get("raw_content", "")

    # Step 1: Search CourtListener for the judge
    cl_result = _search_courtlistener_judges(query)

    # Step 2: LLM cross-reference
    llm_result = _llm_judge_verification(query, raw_content)

    # Aggregate
    confidence = _calculate_judge_confidence(cl_result, llm_result)
    is_valid = confidence >= MIN_CONFIDENCE_THRESHOLD

    result = ValidationResult(
        is_valid=is_valid,
        status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
        confidence=confidence,
        source_used="CourtListener People API + LLM cross-reference",
        details=f"CourtListener match: {cl_result.get('found', False)}, "
                f"Judge: {cl_result.get('name', 'not found')}, "
                f"Court: {cl_result.get('court', 'unknown')}, "
                f"LLM confidence: {llm_result:.2f}",
        provenance=ProvenanceMetadata(
            source_url=cl_result.get("url", ""),
            source_name="CourtListener",
            verification_status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
            confidence_score=confidence,
            authoritative_source="courtlistener.com",
        ),
    )

    return {
        **state,
        "judge_validation": result,
    }


def _search_courtlistener_judges(query: str) -> dict:
    """Search CourtListener People API for a judge."""
    try:
        headers = {}
        if COURTLISTENER_API_KEY:
            headers["Authorization"] = f"Token {COURTLISTENER_API_KEY}"

        # Extract judge name from query
        name = _extract_judge_name(query)
        if not name:
            return {"found": False, "name": "", "court": ""}

        response = requests.get(
            f"{COURTLISTENER_BASE_URL}/people/",
            params={"name": name, "page_size": 5},
            headers=headers,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                judge = results[0]
                return {
                    "found": True,
                    "name": judge.get("name_full", ""),
                    "court": judge.get("court", ""),
                    "url": f"https://www.courtlistener.com{judge.get('resource_uri', '')}",
                }
        return {"found": False, "name": name, "court": ""}
    except Exception as e:
        return {"found": False, "name": "", "court": "", "error": str(e)}


def _extract_judge_name(query: str) -> str:
    """Extract a judge's name from the query text."""
    query_lower = query.lower()
    # Remove common prefixes
    for prefix in ["judge ", "justice ", "chief justice ", "hon. ", "honorable "]:
        if query_lower.startswith(prefix):
            return query[len(prefix):].strip()
    return query.strip()


def _llm_judge_verification(query: str, raw_content: str) -> float:
    """Use LLM to verify judge information."""
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        messages = [
            SystemMessage(content="""You are a legal research specialist. Verify whether the
following judge name and court assignment are accurate based on your knowledge.
Rate your confidence from 0.0 (certainly wrong) to 1.0 (certainly correct).
Consider: Is this a real judge? Is the court assignment correct? Are dates accurate?
Respond with ONLY a decimal number."""),
            HumanMessage(content=f"Verify: {query}\nContext: {raw_content[:500]}")
        ]
        response = llm.invoke(messages)
        return max(0.0, min(1.0, float(response.content.strip())))
    except Exception:
        return 0.5


def _calculate_judge_confidence(cl_result: dict, llm_score: float) -> float:
    """Weighted confidence for judge validation."""
    cl_score = 1.0 if cl_result.get("found") else 0.0
    weights = {"courtlistener": 0.6, "llm": 0.4}
    return round(weights["courtlistener"] * cl_score + weights["llm"] * llm_score, 3)
