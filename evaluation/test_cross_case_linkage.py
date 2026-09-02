import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.vector_retriever import VectorRetriever


def test_cross_case_same_case_exclusion():
    """Results from the current evidence's case must be excluded from potential links."""
    vr = VectorRetriever()
    # Search for evidence_id 1 (which belongs to case_id 1)
    links = vr.find_potential_links(
        evidence_id=1,
        text_chunk="9mm caliber pistol bullet casing forensic ballistics examination report",
        top_k=5,
        similarity_threshold=0.3,
        authorized_case_ids=[1, 2, 3, 4, 5]
    )

    # Current evidence (1) and its case (1) MUST NOT be in the results
    for link in links:
        assert link["linked_evidence_id"] != 1
        assert link["linked_case_id"] != 1


def test_cross_case_rbac_enforcement():
    """Unauthorized cases must never appear in potential cross-case links."""
    vr = VectorRetriever()
    
    # Authorized ONLY for case [2]
    authorized_cases = [2]
    links = vr.find_potential_links(
        evidence_id=1,  # Case 1
        text_chunk="digital forensic disk image analysis report malware hash",
        top_k=5,
        similarity_threshold=0.1,
        authorized_case_ids=authorized_cases
    )

    for link in links:
        assert link["linked_case_id"] in authorized_cases
        assert link["linked_case_id"] != 1


def test_cross_case_empty_or_blank_input():
    """Empty or blank text chunk should return empty list gracefully."""
    vr = VectorRetriever()
    links = vr.find_potential_links(
        evidence_id=1,
        text_chunk="",
        top_k=5
    )
    assert links == []


def test_cross_case_threshold_filtering():
    """Results below the similarity threshold should be filtered out."""
    vr = VectorRetriever()
    # High threshold 0.99 should return empty or only near-exact matches
    high_threshold_links = vr.find_potential_links(
        evidence_id=1,
        text_chunk="unique rare forensic chemical compound XYZ-999",
        top_k=5,
        similarity_threshold=0.99
    )
    assert isinstance(high_threshold_links, list)
    for link in high_threshold_links:
        assert link["similarity_score"] >= 0.99


def test_cross_case_wording_disclaimer():
    """Potential links must use neutral supporting signal wording and not claim definitive connection."""
    vr = VectorRetriever()
    links = vr.find_potential_links(
        evidence_id=1,
        text_chunk="firearm ballistics bullet striation match",
        top_k=5,
        similarity_threshold=0.1
    )

    for link in links:
        assert link["link_type"] == "POTENTIAL_SEMANTIC_LINK"
        assert "NOT forensic proof" in link["explanation"]
        assert "definitely connected" not in link["explanation"].lower()
        assert "same weapon confirmed" not in link["explanation"].lower()
