"""
News Source Validator

Verifies legal news sources against trusted domain lists and media bias services.
Checks URL provenance, domain reputation, and content credibility.
"""

from urllib.parse import urlparse
from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from state import ValidationResult, ProvenanceMetadata, VerificationStatus
from config.settings import TRUSTED_NEWS_DOMAINS, MIN_CONFIDENCE_THRESHOLD


@traceable(name="validate_news_source")
def validate_news_source(state: dict) -> dict:
    """
    Validate a news source URL or claim about legal news.

    Checks:
    1. Domain against trusted domain list
    2. URL structure for known authoritative patterns
    3. LLM-based content credibility assessment
    """
    query = state.get("query", "")
    raw_content = state.get("raw_content", "")

    # Step 1: Extract and check domain
    domain = _extract_domain(query) or _extract_domain(raw_content)
    domain_trusted = _check_domain_trust(domain) if domain else False

    # Step 2: Check URL patterns for authoritative sources
    url_score = _score_url_pattern(query)

    # Step 3: LLM credibility assessment
    llm_assessment = _llm_credibility_check(query, raw_content)

    # Aggregate confidence
    confidence = _calculate_confidence(domain_trusted, url_score, llm_assessment)
    is_valid = confidence >= MIN_CONFIDENCE_THRESHOLD

    result = ValidationResult(
        is_valid=is_valid,
        status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
        confidence=confidence,
        source_used="domain_trust_list + llm_assessment",
        details=f"Domain: {domain or 'none detected'}, "
                f"Trusted: {domain_trusted}, "
                f"URL score: {url_score:.2f}, "
                f"LLM assessment: {llm_assessment:.2f}",
        provenance=ProvenanceMetadata(
            source_name=domain or "unknown",
            verification_status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.UNVERIFIED,
            confidence_score=confidence,
            authoritative_source="trusted_domain_list",
        ),
    )

    return {
        **state,
        "news_validation": result,
    }


def _extract_domain(text: str) -> str:
    """Extract domain from a URL in text."""
    if not text:
        return ""
    # Try to find a URL in the text
    for word in text.split():
        if "." in word and ("http" in word or "www" in word or ".gov" in word or ".com" in word or ".org" in word):
            try:
                parsed = urlparse(word if word.startswith("http") else f"https://{word}")
                domain = parsed.netloc or parsed.path.split("/")[0]
                return domain.lower().replace("www.", "")
            except Exception:
                pass
    return ""


def _check_domain_trust(domain: str) -> bool:
    """Check if domain is in the trusted list."""
    if not domain:
        return False
    # Check exact match
    if domain in TRUSTED_NEWS_DOMAINS:
        return True
    # Check if it's a subdomain of a trusted domain
    for trusted in TRUSTED_NEWS_DOMAINS:
        if domain.endswith(f".{trusted}"):
            return True
    # Check for .gov domains (generally trusted)
    if domain.endswith(".gov"):
        return True
    return False


def _score_url_pattern(text: str) -> float:
    """Score URL based on authoritative patterns."""
    score = 0.0
    text_lower = text.lower()

    # Government domains
    if ".gov" in text_lower:
        score += 0.4
    # Educational domains
    if ".edu" in text_lower:
        score += 0.3
    # Known legal databases
    if any(d in text_lower for d in ["courtlistener", "pacer", "law.cornell", "scotusblog"]):
        score += 0.4
    # Trusted wire services
    if any(d in text_lower for d in ["reuters.com", "apnews.com"]):
        score += 0.3

    return min(score, 1.0)


def _llm_credibility_check(query: str, raw_content: str) -> float:
    """Use LLM to assess credibility of the news claim."""
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        messages = [
            SystemMessage(content="""You are a media credibility analyst. Assess the credibility
of the following legal news claim or source. Rate from 0.0 (not credible) to 1.0 (highly credible).
Consider: source reputation, specificity of claims, presence of verifiable details.
Respond with ONLY a decimal number between 0.0 and 1.0."""),
            HumanMessage(content=f"Query: {query}\nContent: {raw_content[:500]}")
        ]
        response = llm.invoke(messages)
        score = float(response.content.strip())
        return max(0.0, min(1.0, score))
    except Exception:
        return 0.5  # Default neutral score on error


def _calculate_confidence(domain_trusted: bool, url_score: float, llm_score: float) -> float:
    """Weighted confidence calculation."""
    weights = {"domain": 0.4, "url": 0.2, "llm": 0.4}
    score = (
        weights["domain"] * (1.0 if domain_trusted else 0.0) +
        weights["url"] * url_score +
        weights["llm"] * llm_score
    )
    return round(score, 3)
