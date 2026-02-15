"""
Structural Tests for Legal Luminary — targeting uncovered lines
to increase statement coverage to 80%+.

Covers: API call paths (mocked), error handling, edge cases.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from state import create_initial_state, ContentType, VerificationStatus
from validators.news_validator import (
    validate_news_source, _extract_domain, _check_domain_trust,
    _score_url_pattern, _llm_credibility_check, _calculate_confidence,
)
from validators.judge_validator import (
    validate_judge, _search_courtlistener_judges, _extract_judge_name,
    _llm_judge_verification, _calculate_judge_confidence,
)
from validators.official_validator import (
    validate_official, _search_congress_members, _search_fec_candidates,
    _llm_official_verification, _calculate_official_confidence,
)
from validators.election_validator import (
    validate_election, _search_fec_elections, _llm_election_verification,
    _calculate_election_confidence,
)
from validators.law_validator import (
    validate_law, _search_congress_bills, _check_legislation_domain,
    _llm_law_verification, _calculate_law_confidence,
)
from validators.court_doc_validator import (
    validate_court_document, _search_courtlistener_opinions,
    _search_courtlistener_dockets, _check_court_domain,
    _llm_court_doc_verification, _calculate_court_doc_confidence,
)
from validators.template_validator import (
    validate_legal_template, _check_form_registry, _validate_checksum,
    _llm_template_assessment, _calculate_template_confidence,
)


# ============================================================================
# News Validator — structural coverage for _extract_domain edge cases
# ============================================================================
def test_news_extract_domain_www():
    assert _extract_domain("www.reuters.com/article") == "reuters.com"

def test_news_extract_domain_gov():
    assert _extract_domain("something at justice.gov/page") == "justice.gov"

def test_news_url_score_edu():
    assert _score_url_pattern("https://law.cornell.edu/uscode") > 0

def test_news_url_score_multiple():
    score = _score_url_pattern("https://courtlistener.com on reuters.com")
    assert score > 0.3

def test_news_llm_credibility_error():
    """Cover error path in _llm_credibility_check."""
    with patch("validators.news_validator.ChatOpenAI") as mock:
        mock.return_value.invoke.side_effect = Exception("API error")
        score = _llm_credibility_check("test", "content")
    assert score == 0.5

def test_news_domain_subdomain():
    assert _check_domain_trust("opinions.supremecourt.gov") is True

def test_news_domain_empty():
    assert _check_domain_trust("") is False


# ============================================================================
# Judge Validator — structural coverage for API call paths
# ============================================================================
def test_judge_search_cl_success():
    """Cover _search_courtlistener_judges success path."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": [{"name_full": "John Roberts", "court": "scotus", "resource_uri": "/api/rest/v4/people/1/"}]}
    with patch("validators.judge_validator.requests.get", return_value=mock_resp):
        result = _search_courtlistener_judges("John Roberts")
    assert result["found"] is True

def test_judge_search_cl_empty():
    """Cover _search_courtlistener_judges empty results."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": []}
    with patch("validators.judge_validator.requests.get", return_value=mock_resp):
        result = _search_courtlistener_judges("Nonexistent Judge")
    assert result["found"] is False

def test_judge_search_cl_error():
    """Cover _search_courtlistener_judges exception path."""
    with patch("validators.judge_validator.requests.get", side_effect=Exception("timeout")):
        result = _search_courtlistener_judges("test")
    assert result["found"] is False

def test_judge_search_cl_no_name():
    result = _search_courtlistener_judges("")
    assert result["found"] is False

def test_judge_llm_error():
    with patch("validators.judge_validator.ChatOpenAI") as mock:
        mock.return_value.invoke.side_effect = Exception("API error")
        score = _llm_judge_verification("test", "content")
    assert score == 0.5


# ============================================================================
# Official Validator — structural coverage for API paths
# ============================================================================
def test_official_congress_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"members": [{"name": "Cruz", "state": "TX", "partyName": "R", "url": ""}]}
    with patch("validators.official_validator.CONGRESS_GOV_API_KEY", "test_key"):
        with patch("validators.official_validator.requests.get", return_value=mock_resp):
            result = _search_congress_members("Ted Cruz")
    assert result["found"] is True

def test_official_congress_no_key():
    with patch("validators.official_validator.CONGRESS_GOV_API_KEY", ""):
        result = _search_congress_members("test")
    assert result["found"] is False

def test_official_congress_error():
    with patch("validators.official_validator.CONGRESS_GOV_API_KEY", "test_key"):
        with patch("validators.official_validator.requests.get", side_effect=Exception("err")):
            result = _search_congress_members("test")
    assert result["found"] is False

def test_official_fec_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": [{"name": "CRUZ", "office_full": "Senate", "party_full": "R", "candidate_id": "123"}]}
    with patch("validators.official_validator.FEC_API_KEY", "test_key"):
        with patch("validators.official_validator.requests.get", return_value=mock_resp):
            result = _search_fec_candidates("Cruz")
    assert result["found"] is True

def test_official_fec_no_key():
    with patch("validators.official_validator.FEC_API_KEY", ""):
        result = _search_fec_candidates("test")
    assert result["found"] is False

def test_official_fec_error():
    with patch("validators.official_validator.FEC_API_KEY", "test_key"):
        with patch("validators.official_validator.requests.get", side_effect=Exception("err")):
            result = _search_fec_candidates("test")
    assert result["found"] is False

def test_official_llm_error():
    with patch("validators.official_validator.ChatOpenAI") as mock:
        mock.return_value.invoke.side_effect = Exception("API error")
        score = _llm_official_verification("test", "content")
    assert score == 0.5

def test_official_confidence_api_found():
    conf = _calculate_official_confidence({"found": True}, {"found": False}, 0.8)
    assert conf > 0.5


# ============================================================================
# Election Validator — structural coverage
# ============================================================================
def test_election_fec_no_key():
    with patch("validators.election_validator.FEC_API_KEY", ""):
        result = _search_fec_elections("test")
    assert result["found"] is False

def test_election_fec_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": [{"office": "President", "cycle": "2024"}]}
    with patch("validators.election_validator.FEC_API_KEY", "test_key"):
        with patch("validators.election_validator.requests.get", return_value=mock_resp):
            result = _search_fec_elections("2024 Presidential")
    assert result["found"] is True

def test_election_fec_error():
    with patch("validators.election_validator.FEC_API_KEY", "test_key"):
        with patch("validators.election_validator.requests.get", side_effect=Exception("err")):
            result = _search_fec_elections("test")
    assert result["found"] is False

def test_election_llm_error():
    with patch("validators.election_validator.ChatOpenAI") as mock:
        mock.return_value.invoke.side_effect = Exception("API error")
        score = _llm_election_verification("test", "content")
    assert score == 0.5


# ============================================================================
# Law Validator — structural coverage
# ============================================================================
def test_law_congress_no_key():
    with patch("validators.law_validator.CONGRESS_GOV_API_KEY", ""):
        result = _search_congress_bills("test")
    assert result["found"] is False

def test_law_congress_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"bills": [{"title": "Civil Rights Act", "number": "1983", "congress": "42", "url": ""}]}
    with patch("validators.law_validator.CONGRESS_GOV_API_KEY", "test_key"):
        with patch("validators.law_validator.requests.get", return_value=mock_resp):
            result = _search_congress_bills("Civil Rights")
    assert result["found"] is True

def test_law_congress_error():
    with patch("validators.law_validator.CONGRESS_GOV_API_KEY", "test_key"):
        with patch("validators.law_validator.requests.get", side_effect=Exception("err")):
            result = _search_congress_bills("test")
    assert result["found"] is False

def test_law_domain_check():
    assert _check_legislation_domain("See congress.gov for details") is True
    assert _check_legislation_domain("random text") is False

def test_law_llm_error():
    with patch("validators.law_validator.ChatOpenAI") as mock:
        mock.return_value.invoke.side_effect = Exception("API error")
        score = _llm_law_verification("test", "content")
    assert score == 0.5


# ============================================================================
# Court Doc Validator — structural coverage
# ============================================================================
def test_court_doc_opinions_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": [{"caseName": "Brown v Board", "court": "scotus", "dateFiled": "1954", "citation": ["347 U.S. 483"], "absolute_url": "/opinion/1/"}]}
    with patch("validators.court_doc_validator.requests.get", return_value=mock_resp):
        result = _search_courtlistener_opinions("Brown v Board")
    assert result["found"] is True

def test_court_doc_opinions_empty():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": []}
    with patch("validators.court_doc_validator.requests.get", return_value=mock_resp):
        result = _search_courtlistener_opinions("Nonexistent Case")
    assert result["found"] is False

def test_court_doc_opinions_error():
    with patch("validators.court_doc_validator.requests.get", side_effect=Exception("err")):
        result = _search_courtlistener_opinions("test")
    assert result["found"] is False

def test_court_doc_dockets_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": [{"caseName": "Test Case", "docketNumber": "123", "court": "test", "absolute_url": "/docket/1/"}]}
    with patch("validators.court_doc_validator.requests.get", return_value=mock_resp):
        result = _search_courtlistener_dockets("Test Case")
    assert result["found"] is True

def test_court_doc_dockets_error():
    with patch("validators.court_doc_validator.requests.get", side_effect=Exception("err")):
        result = _search_courtlistener_dockets("test")
    assert result["found"] is False

def test_court_doc_domain_check():
    assert _check_court_domain("pacer.gov filing") is True
    assert _check_court_domain("random site") is False

def test_court_doc_llm_error():
    with patch("validators.court_doc_validator.ChatOpenAI") as mock:
        mock.return_value.invoke.side_effect = Exception("API error")
        score = _llm_court_doc_verification("test", "content")
    assert score == 0.5


# ============================================================================
# Template Validator — structural coverage
# ============================================================================
def test_template_registry_general():
    result = _check_form_registry("official court form for filing")
    assert result["found"] is True

def test_template_registry_specific():
    result = _check_form_registry("uscourts.gov/forms AO 440")
    assert result["found"] is True

def test_template_registry_none():
    result = _check_form_registry("random document")
    assert result["found"] is False

def test_template_llm_error():
    with patch("validators.template_validator.ChatOpenAI") as mock:
        mock.return_value.invoke.side_effect = Exception("API error")
        score = _llm_template_assessment("test", "content")
    assert score == 0.5

def test_template_confidence_all_high():
    conf = _calculate_template_confidence({"found": True}, {"valid": True}, 0.9)
    assert conf >= 0.8

def test_template_confidence_all_low():
    conf = _calculate_template_confidence({"found": False}, {"valid": False}, 0.1)
    assert conf < 0.5
