"""
Elected Official Validator

Validates elected officials and their terms using Congress.gov API,
FEC data, and state government sources.
"""

import requests
from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from state import ValidationResult, ProvenanceMetadata, VerificationStatus
from config.settings import (
    CONGRESS_GOV_API_KEY, CONGRESS_GOV_BASE_URL,
    FEC_API_KEY, FEC_BASE_URL, MIN_CONFIDENCE_THRESHOLD,
)


@traceable(name="validate_official")
def validate_official(state: dict) -> dict:
    """
    Validate an elected official's name, office, and term.

    Checks:
    1. Congress.gov API for federal officials
    2. FEC API for candidate records
    3. LLM cross-reference for state/local officials
    """
    query = state.get("query", "")
    raw_content = state.get("raw_content", "")

    # Step 1: Check Congress.gov
    congress_result = _search_congress_members(query)

    # Step 2: Check FEC candidates
    fec_result = _search_fec_candidates(query)

    # Step 3: LLM verification
    llm_score = _llm_official_verification(query, raw_content)

    # Aggregate
    confidence = _calculate_official_confidence(congress_result, fec_result, llm_score)
    is_valid = confidence >= MIN_CONFIDENCE_THRESHOLD

    sources_used = []
    if congress_result.get("found"):
        sources_used.append("Congress.gov")
    if fec_result.get("found"):
        sources_used.append("FEC")
    sources_used.append("LLM")

    result = ValidationResult(
        is_valid=is_valid,
        status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
        confidence=confidence,
        source_used=" + ".join(sources_used),
        details=f"Congress.gov: {congress_result.get('found', False)}, "
                f"FEC: {fec_result.get('found', False)}, "
                f"Name: {congress_result.get('name', fec_result.get('name', 'unknown'))}, "
                f"LLM confidence: {llm_score:.2f}",
        provenance=ProvenanceMetadata(
            source_url=congress_result.get("url", fec_result.get("url", "")),
            source_name="Congress.gov / FEC",
            verification_status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
            confidence_score=confidence,
            authoritative_source="congress.gov / fec.gov",
        ),
    )

    return {
        **state,
        "official_validation": result,
    }


def _search_congress_members(query: str) -> dict:
    """Search Congress.gov for a member of Congress."""
    try:
        if not CONGRESS_GOV_API_KEY:
            return {"found": False, "name": "", "error": "No API key"}

        name = query.strip()
        response = requests.get(
            f"{CONGRESS_GOV_BASE_URL}/member",
            params={"query": name, "limit": 5, "api_key": CONGRESS_GOV_API_KEY},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            members = data.get("members", [])
            if members:
                member = members[0]
                return {
                    "found": True,
                    "name": member.get("name", ""),
                    "state": member.get("state", ""),
                    "party": member.get("partyName", ""),
                    "url": member.get("url", ""),
                }
        return {"found": False, "name": name}
    except Exception as e:
        return {"found": False, "name": "", "error": str(e)}


def _search_fec_candidates(query: str) -> dict:
    """Search FEC for candidate records."""
    try:
        if not FEC_API_KEY:
            return {"found": False, "name": "", "error": "No API key"}

        response = requests.get(
            f"{FEC_BASE_URL}/candidates/search/",
            params={"q": query.strip(), "per_page": 5, "api_key": FEC_API_KEY},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                candidate = results[0]
                return {
                    "found": True,
                    "name": candidate.get("name", ""),
                    "office": candidate.get("office_full", ""),
                    "party": candidate.get("party_full", ""),
                    "url": f"https://www.fec.gov/data/candidate/{candidate.get('candidate_id', '')}/",
                }
        return {"found": False, "name": query.strip()}
    except Exception as e:
        return {"found": False, "name": "", "error": str(e)}


def _llm_official_verification(query: str, raw_content: str) -> float:
    """Use LLM to verify official information."""
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        messages = [
            SystemMessage(content="""You are a political research specialist. Verify whether the
following elected official information is accurate. Rate from 0.0 to 1.0.
Consider: Is this a real official? Is the office correct? Are terms/dates accurate?
Respond with ONLY a decimal number."""),
            HumanMessage(content=f"Verify: {query}\nContext: {raw_content[:500]}")
        ]
        response = llm.invoke(messages)
        return max(0.0, min(1.0, float(response.content.strip())))
    except Exception:
        return 0.5


def _calculate_official_confidence(congress: dict, fec: dict, llm: float) -> float:
    """Weighted confidence for official validation."""
    congress_score = 1.0 if congress.get("found") else 0.0
    fec_score = 1.0 if fec.get("found") else 0.0
    api_score = max(congress_score, fec_score)  # Best API match

    weights = {"api": 0.5, "llm": 0.5}
    if api_score > 0:
        weights = {"api": 0.6, "llm": 0.4}

    return round(weights["api"] * api_score + weights["llm"] * llm, 3)
