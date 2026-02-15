"""
20 Functional Tests based on Equivalence Partitioning (EP)
for the Legal Luminary validation pipeline.

Equivalence Classes:
  EC1:  content_type = valid known type (e.g., "court_document")
  EC2:  content_type = empty string (auto-detect)
  EC3:  content_type = invalid/unknown string
  EC4:  query = valid verifiable citation (e.g., real case)
  EC5:  query = fabricated/hallucinated content
  EC6:  query = empty string
  EC7:  query = prompt injection attempt
  EC8:  raw_content = provided
  EC9:  raw_content = empty
  EC10: source = trusted domain (.gov)
  EC11: source = untrusted/unknown domain
  EC12: source = spoofed domain
  EC13: confidence >= threshold (should verify)
  EC14: confidence < threshold (should reject)
  EC15: judge = real judge name
  EC16: judge = fabricated judge name
  EC17: law = real statute
  EC18: law = fabricated statute
  EC19: official = real elected official
  EC20: official = fabricated official
"""

import pytest
from unittest.mock import patch, MagicMock

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from state import create_initial_state, VerificationStatus, ContentType
from validators.news_validator import (
    validate_news_source, _extract_domain, _check_domain_trust,
    _score_url_pattern, _calculate_confidence,
)
from validators.judge_validator import (
    validate_judge, _extract_judge_name, _calculate_judge_confidence,
)
from validators.official_validator import validate_official, _calculate_official_confidence
from validators.election_validator import validate_election, _calculate_election_confidence
from validators.law_validator import validate_law, _check_legislation_domain, _calculate_law_confidence
from validators.court_doc_validator import (
    validate_court_document, _check_court_domain, _calculate_court_doc_confidence,
)
from validators.template_validator import (
    validate_legal_template, _check_form_registry, _validate_checksum,
    _calculate_template_confidence,
)


# ============================================================================
# TC01: News — trusted .gov domain (EC1, EC4, EC10)
# ============================================================================
def test_TC01_news_trusted_gov_domain():
    """EP: valid type, real .gov source → should have high confidence."""
    state = create_initial_state("news_source", "https://www.supremecourt.gov/opinions")
    with patch("validators.news_validator._llm_credibility_check", return_value=0.9):
        result = validate_news_source(state)
    assert result["news_validation"]["is_valid"] is True
    assert result["news_validation"]["confidence"] >= 0.7


# ============================================================================
# TC02: News — untrusted domain (EC1, EC5, EC11)
# ============================================================================
def test_TC02_news_untrusted_domain():
    """EP: valid type, unknown domain → should have lower confidence."""
    state = create_initial_state("news_source", "https://www.randomfakelegalsite.xyz/article")
    with patch("validators.news_validator._llm_credibility_check", return_value=0.3):
        result = validate_news_source(state)
    assert result["news_validation"]["confidence"] < 0.7


# ============================================================================
# TC03: News — empty query (EC1, EC6, EC9)
# ============================================================================
def test_TC03_news_empty_query():
    """EP: valid type but empty query → should return low confidence."""
    state = create_initial_state("news_source", "")
    with patch("validators.news_validator._llm_credibility_check", return_value=0.3):
        result = validate_news_source(state)
    assert result["news_validation"]["confidence"] < 0.7


# ============================================================================
# TC04: Judge — real judge name (EC1, EC4, EC15)
# ============================================================================
def test_TC04_judge_real_name():
    """EP: real judge name → should verify."""
    state = create_initial_state("judge", "Chief Justice John Roberts")
    with patch("validators.judge_validator._search_courtlistener_judges",
               return_value={"found": True, "name": "John G. Roberts", "court": "Supreme Court", "url": ""}):
        with patch("validators.judge_validator._llm_judge_verification", return_value=0.95):
            result = validate_judge(state)
    assert result["judge_validation"]["is_valid"] is True


# ============================================================================
# TC05: Judge — fabricated name (EC1, EC5, EC16)
# ============================================================================
def test_TC05_judge_fabricated_name():
    """EP: fabricated judge → should reject."""
    state = create_initial_state("judge", "Judge Santa Claus, North Pole Circuit")
    with patch("validators.judge_validator._search_courtlistener_judges",
               return_value={"found": False, "name": "Santa Claus", "court": ""}):
        with patch("validators.judge_validator._llm_judge_verification", return_value=0.1):
            result = validate_judge(state)
    assert result["judge_validation"]["is_valid"] is False


# ============================================================================
# TC06: Official — real senator (EC1, EC4, EC19)
# ============================================================================
def test_TC06_official_real_senator():
    """EP: real elected official → should verify."""
    state = create_initial_state("official", "Senator Ted Cruz, Texas")
    with patch("validators.official_validator._search_congress_members",
               return_value={"found": True, "name": "Ted Cruz", "state": "TX", "party": "R", "url": ""}):
        with patch("validators.official_validator._search_fec_candidates",
                   return_value={"found": True, "name": "CRUZ, TED", "url": ""}):
            with patch("validators.official_validator._llm_official_verification", return_value=0.95):
                result = validate_official(state)
    assert result["official_validation"]["is_valid"] is True


# ============================================================================
# TC07: Official — fabricated official (EC1, EC5, EC20)
# ============================================================================
def test_TC07_official_fabricated():
    """EP: fabricated official → should reject."""
    state = create_initial_state("official", "Senator John Fakename, New Atlantis")
    with patch("validators.official_validator._search_congress_members",
               return_value={"found": False, "name": ""}):
        with patch("validators.official_validator._search_fec_candidates",
                   return_value={"found": False, "name": ""}):
            with patch("validators.official_validator._llm_official_verification", return_value=0.1):
                result = validate_official(state)
    assert result["official_validation"]["is_valid"] is False


# ============================================================================
# TC08: Election — real election data (EC1, EC4)
# ============================================================================
def test_TC08_election_real_data():
    """EP: real election information → should verify."""
    state = create_initial_state("election", "2024 Presidential Election")
    with patch("validators.election_validator._search_fec_elections",
               return_value={"found": True, "election": "President", "cycle": "2024", "url": ""}):
        with patch("validators.election_validator._llm_election_verification", return_value=0.9):
            result = validate_election(state)
    assert result["election_validation"]["is_valid"] is True


# ============================================================================
# TC09: Election — fabricated election (EC1, EC5)
# ============================================================================
def test_TC09_election_fabricated():
    """EP: fabricated election → should reject."""
    state = create_initial_state("election", "2099 Mars Colony Governor Election")
    with patch("validators.election_validator._search_fec_elections",
               return_value={"found": False}):
        with patch("validators.election_validator._llm_election_verification", return_value=0.1):
            result = validate_election(state)
    assert result["election_validation"]["is_valid"] is False


# ============================================================================
# TC10: Law — real federal statute (EC1, EC4, EC17)
# ============================================================================
def test_TC10_law_real_statute():
    """EP: real federal statute → should verify."""
    state = create_initial_state("law", "42 U.S.C. § 1983 - Civil Rights Act")
    with patch("validators.law_validator._search_congress_bills",
               return_value={"found": True, "title": "Civil Rights Act", "url": ""}):
        with patch("validators.law_validator._llm_law_verification", return_value=0.95):
            result = validate_law(state)
    assert result["law_validation"]["is_valid"] is True


# ============================================================================
# TC11: Law — fabricated statute (EC1, EC5, EC18)
# ============================================================================
def test_TC11_law_fabricated():
    """EP: fabricated law → should reject."""
    state = create_initial_state("law", "Unicorn Protection Act, 99 U.S.C. § 9999")
    with patch("validators.law_validator._search_congress_bills",
               return_value={"found": False}):
        with patch("validators.law_validator._llm_law_verification", return_value=0.1):
            result = validate_law(state)
    assert result["law_validation"]["is_valid"] is False


# ============================================================================
# TC12: Court doc — real Supreme Court case (EC1, EC4)
# ============================================================================
def test_TC12_court_doc_real_case():
    """EP: real court case citation → should verify."""
    state = create_initial_state("court_document", "Brown v. Board of Education, 347 U.S. 483 (1954)")
    with patch("validators.court_doc_validator._search_courtlistener_opinions",
               return_value={"found": True, "case_name": "Brown v. Board of Education", "url": ""}):
        with patch("validators.court_doc_validator._search_courtlistener_dockets",
                   return_value={"found": False}):
            with patch("validators.court_doc_validator._llm_court_doc_verification", return_value=0.95):
                result = validate_court_document(state)
    assert result["court_doc_validation"]["is_valid"] is True


# ============================================================================
# TC13: Court doc — fabricated case (EC1, EC5)
# ============================================================================
def test_TC13_court_doc_fabricated():
    """EP: fabricated citation → should reject."""
    state = create_initial_state("court_document", "Fakename v. Imaginary State, 999 U.S. 999 (2099)")
    with patch("validators.court_doc_validator._search_courtlistener_opinions",
               return_value={"found": False}):
        with patch("validators.court_doc_validator._search_courtlistener_dockets",
                   return_value={"found": False}):
            with patch("validators.court_doc_validator._llm_court_doc_verification", return_value=0.1):
                result = validate_court_document(state)
    assert result["court_doc_validation"]["is_valid"] is False


# ============================================================================
# TC14: Template — real court form (EC1, EC4)
# ============================================================================
def test_TC14_template_real_form():
    """EP: real federal court form → should verify."""
    state = create_initial_state("legal_template", "Federal Court Form AO 440 - Summons in a Civil Action")
    with patch("validators.template_validator._llm_template_assessment", return_value=0.85):
        result = validate_legal_template(state)
    assert result["template_validation"]["confidence"] >= 0.5


# ============================================================================
# TC15: Template — fabricated form (EC1, EC5)
# ============================================================================
def test_TC15_template_fabricated():
    """EP: fabricated template → should reject."""
    state = create_initial_state("legal_template", "Form XYZ-9999 Time Travel Permit")
    with patch("validators.template_validator._llm_template_assessment", return_value=0.1):
        result = validate_legal_template(state)
    assert result["template_validation"]["is_valid"] is False


# ============================================================================
# TC16: Domain extraction utility (EC10, EC11)
# ============================================================================
def test_TC16_extract_domain():
    """EP: domain extraction from URLs."""
    assert _extract_domain("https://www.supremecourt.gov/test") == "supremecourt.gov"
    assert _extract_domain("https://randomsite.com/page") == "randomsite.com"
    assert _extract_domain("no url here") == ""


# ============================================================================
# TC17: Domain trust check (EC10, EC11, EC12)
# ============================================================================
def test_TC17_domain_trust():
    """EP: trusted vs untrusted domains."""
    assert _check_domain_trust("supremecourt.gov") is True
    assert _check_domain_trust("uscourts.gov") is True
    assert _check_domain_trust("random-fake.com") is False
    assert _check_domain_trust("something.gov") is True  # .gov = trusted
    assert _check_domain_trust("") is False


# ============================================================================
# TC18: Confidence calculation (EC13, EC14)
# ============================================================================
def test_TC18_confidence_calculation():
    """EP: confidence above/below threshold."""
    # All high → high confidence
    high = _calculate_confidence(True, 0.8, 0.9)
    assert high >= 0.7
    # All low → low confidence
    low = _calculate_confidence(False, 0.0, 0.2)
    assert low < 0.7


# ============================================================================
# TC19: Judge name extraction utility
# ============================================================================
def test_TC19_judge_name_extraction():
    """EP: extracting judge names from various prefixes."""
    assert _extract_judge_name("Judge Sotomayor") == "Sotomayor"
    assert _extract_judge_name("Chief Justice Roberts") == "Roberts"
    assert _extract_judge_name("Hon. Kagan") == "Kagan"
    assert _extract_judge_name("Gorsuch") == "Gorsuch"


# ============================================================================
# TC20: Checksum validation utility
# ============================================================================
def test_TC20_checksum_validation():
    """EP: checksum for template integrity."""
    result_with_content = _validate_checksum("some legal template content")
    assert result_with_content["valid"] is True
    assert len(result_with_content["checksum"]) == 64  # SHA-256 hex

    result_empty = _validate_checksum("")
    assert result_empty["valid"] == "N/A"
