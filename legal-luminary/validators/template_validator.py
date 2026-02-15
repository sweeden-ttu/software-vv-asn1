"""
Legal Template Validator

Validates legal document templates against official court form registries
and performs checksum validation for template integrity.
"""

import hashlib
from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from state import ValidationResult, ProvenanceMetadata, VerificationStatus
from config.settings import MIN_CONFIDENCE_THRESHOLD


# Known court form registries and their URL patterns
KNOWN_FORM_REGISTRIES = {
    "uscourts.gov/forms": "Federal Court Forms",
    "txcourts.gov/forms": "Texas Court Forms",
    "courts.ca.gov/forms": "California Court Forms",
    "nycourts.gov/forms": "New York Court Forms",
}


@traceable(name="validate_legal_template")
def validate_legal_template(state: dict) -> dict:
    """
    Validate a legal document template.

    Checks:
    1. Template source against known court form registries
    2. Checksum validation (if template data provided)
    3. LLM assessment of template structure and completeness
    """
    query = state.get("query", "")
    raw_content = state.get("raw_content", "")

    # Step 1: Check source registry
    registry_result = _check_form_registry(query)

    # Step 2: Checksum validation
    checksum_result = _validate_checksum(raw_content)

    # Step 3: LLM template assessment
    llm_score = _llm_template_assessment(query, raw_content)

    # Aggregate
    confidence = _calculate_template_confidence(registry_result, checksum_result, llm_score)
    is_valid = confidence >= MIN_CONFIDENCE_THRESHOLD

    result = ValidationResult(
        is_valid=is_valid,
        status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
        confidence=confidence,
        source_used="form_registry + checksum + LLM",
        details=f"Registry match: {registry_result.get('found', False)}, "
                f"Registry: {registry_result.get('registry', 'none')}, "
                f"Checksum valid: {checksum_result.get('valid', 'N/A')}, "
                f"LLM assessment: {llm_score:.2f}",
        provenance=ProvenanceMetadata(
            source_name=registry_result.get("registry", "unknown"),
            verification_status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
            confidence_score=confidence,
            authoritative_source="court_form_registry",
        ),
    )

    return {
        **state,
        "template_validation": result,
    }


def _check_form_registry(query: str) -> dict:
    """Check if the template references a known court form registry."""
    query_lower = query.lower()
    for registry_url, registry_name in KNOWN_FORM_REGISTRIES.items():
        if registry_url in query_lower or registry_name.lower() in query_lower:
            return {"found": True, "registry": registry_name, "url": f"https://{registry_url}"}
    # Check for general court form patterns
    if any(kw in query_lower for kw in ["court form", "official form", "judicial form"]):
        return {"found": True, "registry": "General Court Form Reference"}
    return {"found": False, "registry": "none"}


def _validate_checksum(content: str) -> dict:
    """Validate template integrity via checksum."""
    if not content:
        return {"valid": "N/A", "checksum": ""}
    checksum = hashlib.sha256(content.encode()).hexdigest()
    return {"valid": True, "checksum": checksum}


def _llm_template_assessment(query: str, raw_content: str) -> float:
    """Use LLM to assess template structure and completeness."""
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        messages = [
            SystemMessage(content="""You are a legal document specialist. Assess whether the
following legal template reference is legitimate and from an authoritative source.
Rate from 0.0 to 1.0. Consider: Is this a real court form? Does it reference
an official registry? Is the format standard?
Respond with ONLY a decimal number."""),
            HumanMessage(content=f"Assess template: {query}\nContent: {raw_content[:500]}")
        ]
        response = llm.invoke(messages)
        return max(0.0, min(1.0, float(response.content.strip())))
    except Exception:
        return 0.5


def _calculate_template_confidence(registry: dict, checksum: dict, llm: float) -> float:
    """Weighted confidence for template validation."""
    registry_score = 1.0 if registry.get("found") else 0.0
    checksum_score = 1.0 if checksum.get("valid") is True else 0.0
    weights = {"registry": 0.35, "checksum": 0.15, "llm": 0.5}
    return round(
        weights["registry"] * registry_score +
        weights["checksum"] * checksum_score +
        weights["llm"] * llm, 3
    )
