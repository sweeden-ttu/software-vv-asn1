"""
Law and Legislation Validator

Validates laws, statutes, and ordinances against official legislative databases.
Checks Congress.gov for federal laws and provides framework for state/local codes.
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
    TRUSTED_LEGISLATION_DOMAINS, MIN_CONFIDENCE_THRESHOLD,
)


@traceable(name="validate_law")
def validate_law(state: dict) -> dict:
    """
    Validate a law, statute, or ordinance citation.

    Checks:
    1. Congress.gov API for federal legislation
    2. Source URL against trusted legislation domains
    3. LLM cross-reference for citation accuracy
    """
    query = state.get("query", "")
    raw_content = state.get("raw_content", "")

    # Step 1: Search Congress.gov
    congress_result = _search_congress_bills(query)

    # Step 2: Check source domains
    domain_check = _check_legislation_domain(query)

    # Step 3: LLM verification
    llm_score = _llm_law_verification(query, raw_content)

    # Aggregate
    confidence = _calculate_law_confidence(congress_result, domain_check, llm_score)
    is_valid = confidence >= MIN_CONFIDENCE_THRESHOLD

    result = ValidationResult(
        is_valid=is_valid,
        status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
        confidence=confidence,
        source_used="Congress.gov + domain_check + LLM",
        details=f"Congress.gov match: {congress_result.get('found', False)}, "
                f"Bill: {congress_result.get('title', 'not found')}, "
                f"Domain trusted: {domain_check}, "
                f"LLM confidence: {llm_score:.2f}",
        provenance=ProvenanceMetadata(
            source_url=congress_result.get("url", ""),
            source_name="Congress.gov",
            verification_status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
            confidence_score=confidence,
            authoritative_source="congress.gov",
        ),
    )

    return {
        **state,
        "law_validation": result,
    }


def _search_congress_bills(query: str) -> dict:
    """Search Congress.gov for legislation."""
    try:
        if not CONGRESS_GOV_API_KEY:
            return {"found": False, "error": "No API key"}

        response = requests.get(
            f"{CONGRESS_GOV_BASE_URL}/bill",
            params={"query": query.strip(), "limit": 5, "api_key": CONGRESS_GOV_API_KEY},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            bills = data.get("bills", [])
            if bills:
                bill = bills[0]
                return {
                    "found": True,
                    "title": bill.get("title", ""),
                    "number": bill.get("number", ""),
                    "congress": bill.get("congress", ""),
                    "url": bill.get("url", ""),
                }
        return {"found": False}
    except Exception as e:
        return {"found": False, "error": str(e)}


def _check_legislation_domain(text: str) -> bool:
    """Check if any URL in text is from a trusted legislation domain."""
    text_lower = text.lower()
    for domain in TRUSTED_LEGISLATION_DOMAINS:
        if domain in text_lower:
            return True
    return False


def _llm_law_verification(query: str, raw_content: str) -> float:
    """Use LLM to verify law/statute information."""
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        messages = [
            SystemMessage(content="""You are a legal research specialist. Verify whether the
following law, statute, or ordinance citation is accurate. Rate from 0.0 to 1.0.
Consider: Does this law exist? Is the citation format correct? Are details accurate?
Respond with ONLY a decimal number."""),
            HumanMessage(content=f"Verify: {query}\nContext: {raw_content[:500]}")
        ]
        response = llm.invoke(messages)
        return max(0.0, min(1.0, float(response.content.strip())))
    except Exception:
        return 0.5


def _calculate_law_confidence(congress: dict, domain: bool, llm: float) -> float:
    """Weighted confidence for law validation."""
    congress_score = 1.0 if congress.get("found") else 0.0
    domain_score = 1.0 if domain else 0.0
    weights = {"congress": 0.4, "domain": 0.2, "llm": 0.4}
    return round(
        weights["congress"] * congress_score +
        weights["domain"] * domain_score +
        weights["llm"] * llm, 3
    )
