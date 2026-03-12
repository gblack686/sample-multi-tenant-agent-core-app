"""
Unit tests for server/app/hooks/document_gate.py

Pure validation logic — no Bedrock calls, no DynamoDB, no AWS credentials needed.
Tests the _DOC_TYPE_CANONICAL mapping and validate_document_request() function.
"""
import sys
import os
import pytest

# Add server/ to path so app imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.hooks.document_gate import validate_document_request, ValidationResult, _DOC_TYPE_CANONICAL


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sap_ffp(dollar_value: int = 200_000, **kwargs):
    """Default SAP/FFP context — services, non-IT, non-SB."""
    defaults = dict(
        acquisition_method="sap",
        contract_type="ffp",
        dollar_value=dollar_value,
        is_it=False,
        is_services=True,
        is_small_business=False,
        is_rd=False,
    )
    defaults.update(kwargs)
    return defaults


def _micro(**kwargs):
    """Micro-purchase context."""
    defaults = dict(
        acquisition_method="micro",
        contract_type="ffp",
        dollar_value=5_000,
        is_it=False,
        is_services=True,
        is_small_business=False,
        is_rd=False,
    )
    defaults.update(kwargs)
    return defaults


def _negotiated(dollar_value: int = 500_000, **kwargs):
    """Negotiated/FFP context — above SAT."""
    defaults = dict(
        acquisition_method="negotiated",
        contract_type="ffp",
        dollar_value=dollar_value,
        is_it=False,
        is_services=True,
        is_small_business=False,
        is_rd=False,
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# 1. Required doc passes
# ---------------------------------------------------------------------------

def test_required_doc_passes_sow_sap():
    """SOW is required for SAP/$200K services — should pass."""
    result = validate_document_request("sow", **_sap_ffp())
    assert result.action == "pass", f"Expected pass, got {result.action}: {result.reason}"
    assert result.doc_type == "sow"
    assert "required" in result.reason.lower()


def test_required_doc_passes_igce_sap():
    """IGCE is required for SAP — should pass."""
    result = validate_document_request("igce", **_sap_ffp())
    assert result.action == "pass", f"Expected pass, got {result.action}: {result.reason}"


def test_required_doc_passes_market_research_negotiated():
    """Market Research Report is required for negotiated/$500K — should pass."""
    result = validate_document_request("market_research", **_negotiated())
    assert result.action == "pass", f"Expected pass, got {result.action}: {result.reason}"


# ---------------------------------------------------------------------------
# 2. Optional doc warns
# ---------------------------------------------------------------------------

def test_optional_doc_warns_acquisition_plan_sap():
    """Acquisition Plan is NOT required below SAT ($350K) — should warn."""
    result = validate_document_request("acquisition_plan", **_sap_ffp(dollar_value=200_000))
    assert result.action == "warn", f"Expected warn, got {result.action}: {result.reason}"


def test_optional_doc_warns_source_selection_sap():
    """Source Selection Plan is N/A for SAP — should be optional/blocked."""
    result = validate_document_request("eval_criteria", **_sap_ffp())
    # Source Selection Plan is optional (not required) for SAP — either warn or block
    assert result.action in ("warn", "block"), f"Expected warn/block, got {result.action}"


# ---------------------------------------------------------------------------
# 3. Invalid doc blocks
# ---------------------------------------------------------------------------

def test_invalid_doc_warns_source_selection_micro():
    """Source Selection Plan is 'N/A for this method' on micro — matrix lists it
    as optional (not required), so the gate returns warn (not block).
    """
    result = validate_document_request("eval_criteria", **_micro())
    # SSP appears in optional_documents with note "N/A for this method" — warn is correct
    assert result.action == "warn", f"Expected warn, got {result.action}: {result.reason}"
    assert result.doc_type == "eval_criteria"


def test_block_includes_required_docs_list():
    """Block response must include list of required documents for this acquisition.

    Uses an unknown doc type to guarantee a fallback block.
    """
    result = validate_document_request("completely_unknown_doc_type_xyz", **_sap_ffp())
    assert result.action == "block", f"Expected block, got {result.action}: {result.reason}"
    # required_docs should be populated
    assert isinstance(result.required_docs, list)
    assert len(result.required_docs) > 0, "SAP/$200K should have at least one required doc"


def test_block_has_far_citation():
    """Blocked document requests must include a FAR citation.

    Uses an unknown doc type to guarantee a fallback block.
    """
    result = validate_document_request("completely_unknown_doc_type_xyz", **_sap_ffp())
    assert result.action == "block", f"Expected block, got {result.action}: {result.reason}"
    assert result.far_citation, "Expected a FAR citation in block response"


# ---------------------------------------------------------------------------
# 4. Micro-purchase constraints
# ---------------------------------------------------------------------------

def test_micro_purchase_exceeds_threshold_errors():
    """Micro-purchase over $15K triggers matrix error → block."""
    result = validate_document_request("igce", **_micro(dollar_value=20_000))
    # Matrix reports error: "Micro-purchase threshold is $15,000"
    assert result.action == "block"
    assert "15,000" in result.reason or "15K" in result.reason or "micro" in result.reason.lower()


def test_micro_sow_not_required():
    """SOW is NOT required for micro-purchase — should warn or block."""
    result = validate_document_request("sow", **_micro())
    # SOW is optional (not required) for micro-purchase
    assert result.action in ("warn", "block"), f"Expected warn/block, got {result.action}"


# ---------------------------------------------------------------------------
# 5. CR type requires D&F
# ---------------------------------------------------------------------------

def test_cr_type_requires_df():
    """D&F is required for CPFF above SAT — should pass."""
    result = validate_document_request(
        "contract_type_justification",
        acquisition_method="negotiated",
        contract_type="cpff",
        dollar_value=500_000,
        is_it=False,
        is_services=True,
        is_small_business=False,
        is_rd=False,
    )
    assert result.action == "pass", f"Expected pass, got {result.action}: {result.reason}"


# ---------------------------------------------------------------------------
# 6. Sole source requires J&A
# ---------------------------------------------------------------------------

def test_sole_source_requires_ja():
    """J&A is required for sole source — should pass."""
    result = validate_document_request(
        "justification",
        acquisition_method="sole",
        contract_type="ffp",
        dollar_value=200_000,
        is_it=False,
        is_services=True,
        is_small_business=False,
        is_rd=False,
    )
    assert result.action == "pass", f"Expected pass, got {result.action}: {result.reason}"


# ---------------------------------------------------------------------------
# 7. IT requires Section 508
# ---------------------------------------------------------------------------

def test_it_requires_section_508():
    """Section 508 ICT Evaluation is required for IT acquisitions above MPT."""
    result = validate_document_request(
        "section_508",
        acquisition_method="sap",
        contract_type="ffp",
        dollar_value=200_000,
        is_it=True,
        is_services=True,
        is_small_business=False,
        is_rd=False,
    )
    assert result.action == "pass", f"Expected pass, got {result.action}: {result.reason}"


def test_it_requires_security_checklist():
    """IT Security & Privacy Certification is required for IT acquisitions."""
    result = validate_document_request(
        "security_checklist",
        acquisition_method="sap",
        contract_type="ffp",
        dollar_value=200_000,
        is_it=True,
        is_services=True,
        is_small_business=False,
        is_rd=False,
    )
    assert result.action == "pass", f"Expected pass, got {result.action}: {result.reason}"


# ---------------------------------------------------------------------------
# 8. High-value requires Acquisition Plan
# ---------------------------------------------------------------------------

def test_high_value_requires_acquisition_plan():
    """Acquisition Plan is required for acquisitions above $350K (SAT)."""
    result = validate_document_request("acquisition_plan", **_negotiated(dollar_value=500_000))
    assert result.action == "pass", f"Expected pass, got {result.action}: {result.reason}"


# ---------------------------------------------------------------------------
# 9. Canonical mapping covers all doc types
# ---------------------------------------------------------------------------

def test_canonical_mapping_coverage():
    """All entries in _DOC_TYPE_CANONICAL should map to non-empty canonical names."""
    for doc_type, canonical in _DOC_TYPE_CANONICAL.items():
        assert canonical, f"Empty canonical name for doc_type={doc_type}"
        assert len(canonical) > 2, f"Suspiciously short canonical for {doc_type}: {canonical!r}"


# ---------------------------------------------------------------------------
# 10. Return type is always ValidationResult
# ---------------------------------------------------------------------------

def test_validate_always_returns_validation_result():
    """validate_document_request always returns a ValidationResult dataclass."""
    result = validate_document_request("unknown_doc_type", **_sap_ffp())
    assert isinstance(result, ValidationResult)
    assert result.action in ("pass", "warn", "block")
    assert isinstance(result.doc_type, str)
    assert isinstance(result.reason, str)
    assert isinstance(result.required_docs, list)
    assert isinstance(result.optional_docs, list)
