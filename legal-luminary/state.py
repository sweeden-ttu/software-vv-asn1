"""
Core state schema for the Legal Luminary validation pipeline.

The PipelineState flows through every node in the LangGraph. Each validator
reads from and writes to this shared state, adding provenance metadata and
verification results at each stage.
"""

from typing import TypedDict, Optional
from enum import Enum
from datetime import datetime


class VerificationStatus(str, Enum):
    """Status of a verification check."""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    FAILED = "failed"
    PENDING = "pending"
    ESCALATED = "escalated"  # sent to human review


class ContentType(str, Enum):
    """Types of legal/governmental content the pipeline can validate."""
    NEWS_SOURCE = "news_source"
    JUDGE = "judge"
    OFFICIAL = "official"
    ELECTION = "election"
    LAW = "law"
    COURT_DOCUMENT = "court_document"
    LEGAL_TEMPLATE = "legal_template"


class ProvenanceMetadata(TypedDict, total=False):
    """Provenance metadata attached to every verified output."""
    source_url: str
    source_name: str
    retrieval_date: str
    verification_date: str
    verification_status: str
    confidence_score: float
    authoritative_source: str
    notes: str


class ValidationResult(TypedDict, total=False):
    """Result of a single validation check."""
    is_valid: bool
    status: str
    confidence: float
    source_used: str
    details: str
    provenance: ProvenanceMetadata


class PipelineState(TypedDict, total=False):
    """
    Shared state for the entire validation pipeline.

    Each validator reads `content_type`, `query`, and `raw_content`,
    then writes its results into the appropriate validation field.
    """
    # --- Input ---
    content_type: str               # One of ContentType values
    query: str                      # The claim or content to validate
    raw_content: str                # Raw LLM-generated content to verify

    # --- Classification ---
    detected_content_type: str      # Auto-detected content type
    classification_confidence: float

    # --- Validator Results ---
    news_validation: ValidationResult
    judge_validation: ValidationResult
    official_validation: ValidationResult
    election_validation: ValidationResult
    law_validation: ValidationResult
    court_doc_validation: ValidationResult
    template_validation: ValidationResult

    # --- Pipeline Control ---
    retry_count: int
    max_retries: int
    should_retry: bool
    escalate_to_human: bool

    # --- Aggregate Output ---
    overall_status: str             # "verified", "unverified", "failed"
    overall_confidence: float
    provenance: ProvenanceMetadata
    verified_content: str           # Content only if verified
    error_message: str


def create_initial_state(content_type: str, query: str, raw_content: str = "") -> PipelineState:
    """Factory function to create a properly initialized pipeline state."""
    return PipelineState(
        content_type=content_type,
        query=query,
        raw_content=raw_content,
        detected_content_type="",
        classification_confidence=0.0,
        news_validation={},
        judge_validation={},
        official_validation={},
        election_validation={},
        law_validation={},
        court_doc_validation={},
        template_validation={},
        retry_count=0,
        max_retries=3,
        should_retry=False,
        escalate_to_human=False,
        overall_status="pending",
        overall_confidence=0.0,
        provenance={},
        verified_content="",
        error_message="",
    )
