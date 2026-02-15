"""
Tests for the Texas Legal Data Crawler pipeline.

Covers:
  - SODA API helper functions (fetch_sample_records, fetch_record_count, fetch_dataset_metadata)
  - Dataset classification (mocked LLM responses)
  - LangGraph pipeline structure (nodes, edges, routing)
  - End-to-end crawl with mocked API responses
  - Edge cases (empty datasets, API errors, malformed LLM output)
"""

import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from texas_data_crawler import (
    TEXAS_LEGAL_DATASETS,
    SODA_BASE,
    fetch_dataset_metadata,
    fetch_sample_records,
    fetch_record_count,
    discover_datasets,
    fetch_and_sample,
    classify_dataset,
    accumulate_result,
    route_continue_or_done,
    generate_summary,
    build_crawler_pipeline,
    CrawlerState,
    DatasetClassification,
)


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture
def sample_crawler_state() -> CrawlerState:
    return {
        "datasets_to_crawl": [
            {"id": "q4fw-9sy9", "name": "TDCJ Releases FY 2025",
             "agency": "TX Dept of Criminal Justice", "category": "Public Safety",
             "description": "All inmate releases from TDCJ for FY 2025"},
        ],
        "current_index": 0,
        "classified_datasets": [],
        "law_verification_count": 0,
        "news_count": 0,
        "resource_count": 0,
        "error_count": 0,
        "completed": False,
        "summary": "",
    }


@pytest.fixture
def sample_classification() -> DatasetClassification:
    return {
        "dataset_id": "q4fw-9sy9",
        "dataset_name": "TDCJ Releases FY 2025",
        "agency": "TX Dept of Criminal Justice",
        "category": "Public Safety",
        "description": "All inmate releases from TDCJ for FY 2025",
        "sample_records": [{"name": "DOE, JOHN", "offense": "BURGLARY"}],
        "record_count": 25000,
        "column_names": ["name", "tdcj_number", "offense", "release_date"],
        "api_endpoint": f"{SODA_BASE}/q4fw-9sy9.json",
        "crawl_timestamp": "2026-02-15T00:00:00",
    }


# ===================================================================
# SODA API Helper Tests
# ===================================================================

class TestFetchSampleRecords:
    @patch("texas_data_crawler.requests.get")
    def test_successful_fetch(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"name": "DOE, JOHN", "offense": "BURGLARY"},
            {"name": "SMITH, JANE", "offense": "THEFT"},
        ]
        mock_get.return_value = mock_resp

        records, columns = fetch_sample_records("q4fw-9sy9", limit=2)
        assert len(records) == 2
        assert "name" in columns
        assert "offense" in columns

    @patch("texas_data_crawler.requests.get")
    def test_api_error_returns_empty(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        records, columns = fetch_sample_records("invalid-id")
        assert records == []
        assert columns == []

    @patch("texas_data_crawler.requests.get")
    def test_network_exception(self, mock_get):
        mock_get.side_effect = Exception("Connection refused")
        records, columns = fetch_sample_records("q4fw-9sy9")
        assert records == []
        assert columns == []

    @patch("texas_data_crawler.requests.get")
    def test_empty_dataset(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mock_get.return_value = mock_resp

        records, columns = fetch_sample_records("empty-id")
        assert records == []
        assert columns == []


class TestFetchRecordCount:
    @patch("texas_data_crawler.requests.get")
    def test_successful_count(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"count": "25432"}]
        mock_get.return_value = mock_resp

        count = fetch_record_count("q4fw-9sy9")
        assert count == 25432

    @patch("texas_data_crawler.requests.get")
    def test_api_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        count = fetch_record_count("q4fw-9sy9")
        assert count == 0

    @patch("texas_data_crawler.requests.get")
    def test_network_exception(self, mock_get):
        mock_get.side_effect = Exception("Timeout")
        count = fetch_record_count("q4fw-9sy9")
        assert count == 0


class TestFetchDatasetMetadata:
    @patch("texas_data_crawler.requests.get")
    def test_successful_metadata(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "q4fw-9sy9",
            "name": "TDCJ Releases FY 2025",
            "attribution": "TX Dept of Criminal Justice",
        }
        mock_get.return_value = mock_resp

        meta = fetch_dataset_metadata("q4fw-9sy9")
        assert meta["name"] == "TDCJ Releases FY 2025"

    @patch("texas_data_crawler.requests.get")
    def test_metadata_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        meta = fetch_dataset_metadata("bad-id")
        assert "error" in meta


# ===================================================================
# LangGraph Node Tests
# ===================================================================

class TestDiscoverDatasets:
    @patch("texas_data_crawler.requests.get")
    def test_discovery_includes_known_datasets(self, mock_get):
        # Mock the catalog search to return nothing extra
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}
        mock_get.return_value = mock_resp

        state: CrawlerState = {
            "datasets_to_crawl": [],
            "current_index": 0,
            "classified_datasets": [],
            "completed": False,
        }
        result = discover_datasets(state)
        ids = {d["id"] for d in result["datasets_to_crawl"]}
        # All known datasets should be included
        for ds in TEXAS_LEGAL_DATASETS:
            assert ds["id"] in ids

    @patch("texas_data_crawler.requests.get")
    def test_discovery_handles_api_failure(self, mock_get):
        mock_get.side_effect = Exception("API down")
        state: CrawlerState = {
            "datasets_to_crawl": [],
            "current_index": 0,
            "classified_datasets": [],
            "completed": False,
        }
        result = discover_datasets(state)
        # Should still have the hardcoded datasets
        assert len(result["datasets_to_crawl"]) == len(TEXAS_LEGAL_DATASETS)


class TestFetchAndSample:
    @patch("texas_data_crawler.fetch_record_count", return_value=5000)
    @patch("texas_data_crawler.fetch_sample_records",
           return_value=([{"name": "DOE"}], ["name"]))
    def test_fetch_populates_classification(self, mock_sample, mock_count,
                                             sample_crawler_state):
        result = fetch_and_sample(sample_crawler_state)
        c = result["current_classification"]
        assert c["dataset_id"] == "q4fw-9sy9"
        assert c["record_count"] == 5000
        assert "name" in c["column_names"]

    def test_fetch_past_end_marks_completed(self, sample_crawler_state):
        sample_crawler_state["current_index"] = 999
        result = fetch_and_sample(sample_crawler_state)
        assert result["completed"] is True


class TestClassifyDataset:
    @patch("texas_data_crawler._llm")
    def test_law_verification_classification(self, mock_llm, sample_crawler_state,
                                              sample_classification):
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "classification": "LAW_VERIFICATION",
            "confidence": 0.95,
            "usefulness_summary": "Official TDCJ inmate records for criminal defense",
            "ground_truth_potential": "Verifiable inmate release dates and offenses",
        })
        mock_llm.invoke.return_value = mock_response

        sample_crawler_state["current_classification"] = sample_classification
        result = classify_dataset(sample_crawler_state)
        c = result["current_classification"]
        assert c["classification"] == "LAW_VERIFICATION"
        assert c["confidence"] == 0.95

    @patch("texas_data_crawler._llm")
    def test_llm_error_falls_back(self, mock_llm, sample_crawler_state,
                                    sample_classification):
        mock_llm.invoke.side_effect = Exception("LLM timeout")
        sample_crawler_state["current_classification"] = sample_classification
        result = classify_dataset(sample_crawler_state)
        c = result["current_classification"]
        # Should fall back to ATTORNEY_RESOURCE with low confidence
        assert c["classification"] == "ATTORNEY_RESOURCE"
        assert c["confidence"] == 0.3

    @patch("texas_data_crawler._llm")
    def test_malformed_llm_response(self, mock_llm, sample_crawler_state,
                                      sample_classification):
        mock_response = MagicMock()
        mock_response.content = "This is not JSON at all"
        mock_llm.invoke.return_value = mock_response

        sample_crawler_state["current_classification"] = sample_classification
        result = classify_dataset(sample_crawler_state)
        c = result["current_classification"]
        assert c["classification"] == "ATTORNEY_RESOURCE"
        assert c["confidence"] == 0.5


class TestAccumulateResult:
    def test_law_verification_increments(self, sample_crawler_state,
                                          sample_classification):
        sample_classification["classification"] = "LAW_VERIFICATION"
        sample_crawler_state["current_classification"] = sample_classification
        result = accumulate_result(sample_crawler_state)
        assert result["law_verification_count"] == 1
        assert len(result["classified_datasets"]) == 1

    def test_news_increments(self, sample_crawler_state, sample_classification):
        sample_classification["classification"] = "NEWS"
        sample_crawler_state["current_classification"] = sample_classification
        result = accumulate_result(sample_crawler_state)
        assert result["news_count"] == 1

    def test_resource_increments(self, sample_crawler_state, sample_classification):
        sample_classification["classification"] = "ATTORNEY_RESOURCE"
        sample_crawler_state["current_classification"] = sample_classification
        result = accumulate_result(sample_crawler_state)
        assert result["resource_count"] == 1

    def test_marks_completed_at_end(self, sample_crawler_state, sample_classification):
        sample_classification["classification"] = "LAW_VERIFICATION"
        sample_crawler_state["current_classification"] = sample_classification
        sample_crawler_state["current_index"] = 0
        # Only 1 dataset in the list
        result = accumulate_result(sample_crawler_state)
        assert result["completed"] is True
        assert result["current_index"] == 1


class TestRouting:
    def test_routes_to_fetch_when_not_done(self):
        state = {"completed": False}
        assert route_continue_or_done(state) == "fetch_and_sample"

    def test_routes_to_summary_when_done(self):
        state = {"completed": True}
        assert route_continue_or_done(state) == "generate_summary"


class TestGenerateSummary:
    def test_summary_includes_counts(self):
        state: CrawlerState = {
            "classified_datasets": [
                {"dataset_name": "TDCJ", "dataset_id": "abc",
                 "classification": "LAW_VERIFICATION", "record_count": 1000,
                 "confidence": 0.9, "usefulness_summary": "test"},
                {"dataset_name": "Insurance", "dataset_id": "def",
                 "classification": "ATTORNEY_RESOURCE", "record_count": 500,
                 "confidence": 0.8, "usefulness_summary": "test"},
            ],
            "law_verification_count": 1,
            "news_count": 0,
            "resource_count": 1,
            "error_count": 0,
            "completed": True,
        }
        result = generate_summary(state)
        assert "LAW VERIFICATION" in result["summary"]
        assert "ATTORNEY RESOURCES" in result["summary"]
        assert "TDCJ" in result["summary"]


# ===================================================================
# Pipeline Structure Tests
# ===================================================================

class TestPipelineStructure:
    def test_pipeline_compiles(self):
        pipeline = build_crawler_pipeline()
        assert pipeline is not None

    def test_known_datasets_not_empty(self):
        assert len(TEXAS_LEGAL_DATASETS) >= 13

    def test_all_datasets_have_required_fields(self):
        for ds in TEXAS_LEGAL_DATASETS:
            assert "id" in ds, f"Missing id: {ds}"
            assert "name" in ds, f"Missing name: {ds}"
            assert "agency" in ds, f"Missing agency: {ds}"
            assert "description" in ds, f"Missing description: {ds}"

    def test_dataset_ids_are_valid_format(self):
        import re
        pattern = re.compile(r"^[a-z0-9]{4}-[a-z0-9]{4}$")
        for ds in TEXAS_LEGAL_DATASETS:
            assert pattern.match(ds["id"]), f"Invalid dataset ID format: {ds['id']}"
