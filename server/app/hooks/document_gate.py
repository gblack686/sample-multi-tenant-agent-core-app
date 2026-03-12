"""Document gating logic — validates doc_type against acquisition context.

Pure functions, no side effects. Called by EagleSSEHookProvider.BeforeToolCallEvent.
Ported from docs/contract-requirements-matrix.html (JavaScript).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    action: str                      # "pass" | "warn" | "block"
    doc_type: str
    reason: str
    far_citation: str = ""
    required_docs: list = field(default_factory=list)
    optional_docs: list = field(default_factory=list)


# Map internal doc_type IDs to canonical names used by contract_matrix.get_requirements()
_DOC_TYPE_CANONICAL: dict[str, str] = {
    "sow": "SOW / PWS",
    "pws": "SOW / PWS",
    "igce": "IGCE",
    "market_research": "Market Research",
    "acquisition_plan": "Acquisition Plan",
    "justification": "J&A / Justification",
    "ja": "J&A / Justification",
    "eval_criteria": "Source Selection Plan",
    "source_selection_plan": "Source Selection Plan",
    "security_checklist": "IT Security & Privacy Certification",
    "section_508": "Section 508 ICT Evaluation",
    "cor_certification": "QASP",
    "qasp": "QASP",
    "contract_type_justification": "D&F (Determination & Findings)",
    "df": "D&F (Determination & Findings)",
    "subcontracting_plan": "Subcontracting Plan",
    "small_business_review": "HHS-653 Small Business Review",
    "purchase_request": "Purchase Request",
}


def _doc_matches(canonical: str, doc_name: str, doc_type: str) -> bool:
    """Return True if canonical name or doc_type alias matches a matrix doc name."""
    doc_name_lower = doc_name.lower()
    # Exact canonical match
    if canonical.lower() == doc_name_lower:
        return True
    # Substring match — handles "Market Research" matching "Market Research Report"
    if canonical.lower() in doc_name_lower:
        return True
    if doc_name_lower in canonical.lower():
        return True
    # Raw doc_type as substring fallback
    if doc_type.replace("_", " ").lower() in doc_name_lower:
        return True
    return False


def validate_document_request(
    doc_type: str,
    acquisition_method: str,
    contract_type: str,
    dollar_value: int,
    is_it: bool = False,
    is_services: bool = True,
    is_small_business: bool = False,
    is_rd: bool = False,
) -> ValidationResult:
    """Validate whether doc_type is appropriate for the acquisition context.

    Uses contract_matrix.get_requirements() to get the authoritative doc list,
    then checks if the requested doc_type is required, optional, or invalid.

    Args:
        doc_type: Internal document type identifier (e.g. "sow", "igce").
        acquisition_method: Acquisition method (micro, sap, negotiated, fss, sole, etc.).
        contract_type: Contract type (ffp, cpff, tm, etc.).
        dollar_value: Estimated dollar value in USD.
        is_it: Whether this is an IT acquisition.
        is_services: Whether this is a services acquisition.
        is_small_business: Whether small business set-aside applies.
        is_rd: Whether this involves research and development.

    Returns:
        ValidationResult with action="pass", "warn", or "block".
    """
    from ..tools.contract_matrix import get_requirements

    reqs = get_requirements(
        dollar_value=dollar_value,
        method=acquisition_method,
        contract_type=contract_type,
        is_it=is_it,
        is_services=is_services,
        is_small_business=is_small_business,
        is_rd=is_rd,
    )

    required_names = [d["name"] for d in reqs["required_documents"]]
    optional_names = [d["name"] for d in reqs["optional_documents"]]
    canonical = _DOC_TYPE_CANONICAL.get(doc_type, doc_type.replace("_", " ").title())

    # Check matrix errors first (e.g., micro-purchase > $15K)
    if reqs.get("errors"):
        return ValidationResult(
            action="block",
            doc_type=doc_type,
            reason="; ".join(reqs["errors"]),
            far_citation="See FAR Part 13 for simplified acquisition thresholds",
            required_docs=required_names,
            optional_docs=optional_names,
        )

    # Check required docs
    for doc in reqs["required_documents"]:
        if _doc_matches(canonical, doc["name"], doc_type):
            return ValidationResult(
                action="pass",
                doc_type=doc_type,
                reason=f"{doc['name']} is required for this acquisition",
                far_citation=doc.get("note", ""),
                required_docs=required_names,
                optional_docs=optional_names,
            )

    # Check optional docs
    for doc in reqs["optional_documents"]:
        if _doc_matches(canonical, doc["name"], doc_type):
            return ValidationResult(
                action="warn",
                doc_type=doc_type,
                reason=(
                    f"{doc['name']} is optional for this acquisition scenario. "
                    f"{doc.get('note', '')}"
                ).strip(),
                far_citation=doc.get("note", ""),
                required_docs=required_names,
                optional_docs=optional_names,
            )

    # Not found in either list — block with a helpful explanation
    method_label = acquisition_method.upper().replace("-", " ")
    value_fmt = f"${dollar_value:,}"
    return ValidationResult(
        action="block",
        doc_type=doc_type,
        reason=(
            f"{canonical} is not required or applicable for "
            f"method={method_label}, type={contract_type.upper()}, "
            f"value={value_fmt}. "
            f"Required documents for this acquisition: {', '.join(required_names) or 'none'}."
        ),
        far_citation="See FAR Part 4.803 for contract file requirements",
        required_docs=required_names,
        optional_docs=optional_names,
    )
