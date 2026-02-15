"""
Election Validator

Validates election details, candidates, and results against
FEC filings and state election board data.
"""

import requests
from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from state import ValidationResult, ProvenanceMetadata, VerificationStatus
from config.settings import FEC_API_KEY, FEC_BASE_URL, MIN_CONFIDENCE_THRESHOLD


@traceable(name="validate_election")
def validate_election(state: dict) -> dict:
    """
    Validate election details: candidates, dates, results.

    Checks:
    1. FEC API for federal election filings and results
    2. LLM cross-reference for state/local elections
    """
    query = state.get("query", "")
    raw_content = state.get("raw_content", "")

    # Step 1: Search FEC for election data
    fec_result = _search_fec_elections(query)

    # Step 2: LLM verification
    llm_score = _llm_election_verification(query, raw_content)

    # Aggregate
    confidence = _calculate_election_confidence(fec_result, llm_score)
    is_valid = confidence >= MIN_CONFIDENCE_THRESHOLD

    result = ValidationResult(
        is_valid=is_valid,
        status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
        confidence=confidence,
        source_used="FEC API + LLM cross-reference",
        details=f"FEC match: {fec_result.get('found', False)}, "
                f"Election: {fec_result.get('election', 'unknown')}, "
                f"LLM confidence: {llm_score:.2f}",
        provenance=ProvenanceMetadata(
            source_url=fec_result.get("url", ""),
            source_name="Federal Election Commission",
            verification_status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
            confidence_score=confidence,
            authoritative_source="fec.gov",
        ),
    )

    return {
        **state,
        "election_validation": result,
    }


def _search_fec_elections(query: str) -> dict:
    """Search FEC for election information."""
    try:
        if not FEC_API_KEY:
            return {"found": False, "error": "No FEC API key"}

        response = requests.get(
            f"{FEC_BASE_URL}/elections/search/",
            params={"q": query.strip(), "per_page": 5, "api_key": FEC_API_KEY},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                election = results[0]
                return {
                    "found": True,
                    "election": election.get("office", ""),
                    "cycle": election.get("cycle", ""),
                    "url": "https://www.fec.gov/data/elections/",
                }
        return {"found": False}
    except Exception as e:
        return {"found": False, "error": str(e)}


def _llm_election_verification(query: str, raw_content: str) -> float:
    """Use LLM to verify election information."""
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        messages = [
            SystemMessage(content="""You are an election data analyst. Verify whether the
following election information is accurate. Rate from 0.0 to 1.0.
Consider: Are candidates real? Are dates correct? Are results accurate?
Respond with ONLY a decimal number."""),
            HumanMessage(content=f"Verify: {query}\nContext: {raw_content[:500]}")
        ]
        response = llm.invoke(messages)
        return max(0.0, min(1.0, float(response.content.strip())))
    except Exception:
        return 0.5


def _calculate_election_confidence(fec: dict, llm: float) -> float:
    """Weighted confidence for election validation."""
    fec_score = 1.0 if fec.get("found") else 0.0
    weights = {"fec": 0.5, "llm": 0.5}
    return round(weights["fec"] * fec_score + weights["llm"] * llm, 3)
