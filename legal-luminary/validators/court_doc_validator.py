"""
Court Document Validator

Validates court documents (filings, opinions, dockets) against
CourtListener API, PACER, and state court systems.
"""

import requests
from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from state import ValidationResult, ProvenanceMetadata, VerificationStatus
from config.settings import (
    COURTLISTENER_API_KEY, COURTLISTENER_BASE_URL,
    TRUSTED_COURT_DOMAINS, MIN_CONFIDENCE_THRESHOLD,
)


@traceable(name="validate_court_document")
def validate_court_document(state: dict) -> dict:
    """
    Validate a court document citation or reference.

    Checks:
    1. CourtListener Search API for opinions and dockets
    2. Domain trust for court document URLs
    3. LLM cross-reference for citation format and accuracy
    """
    query = state.get("query", "")
    raw_content = state.get("raw_content", "")

    # Step 1: Search CourtListener
    cl_result = _search_courtlistener_opinions(query)

    # Step 2: Search CourtListener dockets
    docket_result = _search_courtlistener_dockets(query)

    # Step 3: Domain trust check
    domain_trusted = _check_court_domain(query)

    # Step 4: LLM citation verification
    llm_score = _llm_court_doc_verification(query, raw_content)

    # Aggregate
    api_found = cl_result.get("found", False) or docket_result.get("found", False)
    confidence = _calculate_court_doc_confidence(api_found, domain_trusted, llm_score)
    is_valid = confidence >= MIN_CONFIDENCE_THRESHOLD

    result = ValidationResult(
        is_valid=is_valid,
        status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
        confidence=confidence,
        source_used="CourtListener API + domain_check + LLM",
        details=f"CourtListener opinion: {cl_result.get('found', False)}, "
                f"Docket: {docket_result.get('found', False)}, "
                f"Case: {cl_result.get('case_name', docket_result.get('case_name', 'unknown'))}, "
                f"Domain trusted: {domain_trusted}, "
                f"LLM confidence: {llm_score:.2f}",
        provenance=ProvenanceMetadata(
            source_url=cl_result.get("url", docket_result.get("url", "")),
            source_name="CourtListener",
            verification_status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
            confidence_score=confidence,
            authoritative_source="courtlistener.com",
        ),
    )

    return {
        **state,
        "court_doc_validation": result,
    }


def _search_courtlistener_opinions(query: str) -> dict:
    """Search CourtListener for court opinions."""
    try:
        headers = {}
        if COURTLISTENER_API_KEY:
            headers["Authorization"] = f"Token {COURTLISTENER_API_KEY}"

        response = requests.get(
            f"{COURTLISTENER_BASE_URL}/search/",
            params={"q": query.strip(), "type": "o", "page_size": 5},
            headers=headers,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                opinion = results[0]
                return {
                    "found": True,
                    "case_name": opinion.get("caseName", ""),
                    "court": opinion.get("court", ""),
                    "date_filed": opinion.get("dateFiled", ""),
                    "citation": opinion.get("citation", []),
                    "url": f"https://www.courtlistener.com{opinion.get('absolute_url', '')}",
                }
        return {"found": False}
    except Exception as e:
        return {"found": False, "error": str(e)}


def _search_courtlistener_dockets(query: str) -> dict:
    """Search CourtListener for docket entries."""
    try:
        headers = {}
        if COURTLISTENER_API_KEY:
            headers["Authorization"] = f"Token {COURTLISTENER_API_KEY}"

        response = requests.get(
            f"{COURTLISTENER_BASE_URL}/search/",
            params={"q": query.strip(), "type": "r", "page_size": 5},
            headers=headers,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                docket = results[0]
                return {
                    "found": True,
                    "case_name": docket.get("caseName", ""),
                    "docket_number": docket.get("docketNumber", ""),
                    "court": docket.get("court", ""),
                    "url": f"https://www.courtlistener.com{docket.get('absolute_url', '')}",
                }
        return {"found": False}
    except Exception as e:
        return {"found": False, "error": str(e)}


def _check_court_domain(text: str) -> bool:
    """Check if text references a trusted court domain."""
    text_lower = text.lower()
    for domain in TRUSTED_COURT_DOMAINS:
        if domain in text_lower:
            return True
    return False


def _llm_court_doc_verification(query: str, raw_content: str) -> float:
    """Use LLM to verify court document citation."""
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        messages = [
            SystemMessage(content="""You are a legal citation specialist. Verify whether the
following court document reference is accurate. Rate from 0.0 to 1.0.
Consider: Does this case exist? Is the citation format correct (e.g., Bluebook)?
Are the parties, court, and year correct?
Respond with ONLY a decimal number."""),
            HumanMessage(content=f"Verify: {query}\nContext: {raw_content[:500]}")
        ]
        response = llm.invoke(messages)
        return max(0.0, min(1.0, float(response.content.strip())))
    except Exception:
        return 0.5


def _calculate_court_doc_confidence(api_found: bool, domain: bool, llm: float) -> float:
    """Weighted confidence for court document validation."""
    api_score = 1.0 if api_found else 0.0
    domain_score = 1.0 if domain else 0.0
    weights = {"api": 0.4, "domain": 0.2, "llm": 0.4}
    return round(
        weights["api"] * api_score +
        weights["domain"] * domain_score +
        weights["llm"] * llm, 3
    )
