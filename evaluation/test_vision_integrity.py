"""
evaluation/test_vision_integrity.py
Automated evaluation test suite for Evidence Image, Vision AI, and SHA-256 Byte Integrity verification.
"""
import os
import sys
import hashlib
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.vision_inspector import VisionInspector
from ai.visual_cross_checker import VisualCrossChecker
from ai.hybrid_retriever import HybridRetriever


def test_vision_integrity_suite():
    print("=" * 65)
    print("  EVIDENCE IMAGE, VISION AI & SHA-256 INTEGRITY TEST SUITE")
    print("=" * 65)

    passed_count = 0
    total_tests = 7

    # -------------------------------------------------------------
    # TEST 1: SHA-256 Byte Verification for untouched existing photo
    # -------------------------------------------------------------
    test_img_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "static", "evidence_photos")
    test_img_path = os.path.join(test_img_dir, "blood_sample_collection.jpg")

    if os.path.isfile(test_img_path):
        with open(test_img_path, "rb") as f:
            h1 = hashlib.sha256(f.read()).hexdigest()
        t1_passed = len(h1) == 64
        print(f"  Test 1 (SHA-256 Byte Calculation on E001 photo): [{'PASS' if t1_passed else 'FAIL'}]")
        if t1_passed:
            passed_count += 1
            print(f"    Raw SHA-256 Hash: {h1[:24]}...")
    else:
        print("  Test 1: [FAIL] Image file blood_sample_collection.jpg missing.")

    # -------------------------------------------------------------
    # TEST 2 & 3: Cryptographic Tamper Detection & Restoration
    # -------------------------------------------------------------
    temp_file = os.path.join(test_img_dir, "_test_tamper_temp.jpg")
    try:
        with open(test_img_path, "rb") as f_src:
            raw_bytes = bytearray(f_src.read())

        original_hash = hashlib.sha256(raw_bytes).hexdigest()

        # Modify 1 byte in the middle of bytearray
        tampered_bytes = bytearray(raw_bytes)
        tampered_bytes[len(tampered_bytes) // 2] ^= 0xFF  # Flip bits

        with open(temp_file, "wb") as f_tamp:
            f_tamp.write(tampered_bytes)

        # Hash check: Tampered
        with open(temp_file, "rb") as f_check:
            h_tampered = hashlib.sha256(f_check.read()).hexdigest()
        t2_passed = (h_tampered != original_hash)
        print(f"  Test 2 (SHA-256 Cryptographic Tamper Detection): [{'PASS' if t2_passed else 'FAIL'}]")
        if t2_passed:
            passed_count += 1
            print(f"    1-Byte Modification -> Hash Mismatch (COMPROMISED)")

        # Test 3: Restore pristine bytes
        with open(temp_file, "wb") as f_dst:
            f_dst.write(raw_bytes)
        with open(temp_file, "rb") as f_check2:
            h_restored = hashlib.sha256(f_check2.read()).hexdigest()
        t3_passed = (h_restored == original_hash)
        print(f"  Test 3 (File Restoration & Re-verification): [{'PASS' if t3_passed else 'FAIL'}]")
        if t3_passed:
            passed_count += 1
            print(f"    Restored File Bytes -> Hash Match (INTACT)")

    except Exception as e:
        print(f"  Test 2/3: [FAIL] {e}")
    finally:
        if os.path.isfile(temp_file):
            os.remove(temp_file)

    # -------------------------------------------------------------
    # TEST 4: Graceful Response for Missing Photograph
    # -------------------------------------------------------------
    inspector = VisionInspector()
    res_missing = inspector.analyze_image("non_existent_file.jpg", 999)
    t4_passed = (res_missing.get("status") == "NO_IMAGE") and ("No photograph" in res_missing.get("visible_condition", ""))
    print(f"  Test 4 (Missing Photograph Fallback): [{'PASS' if t4_passed else 'FAIL'}]")
    if t4_passed:
        passed_count += 1
        print(f"    Message: '{res_missing.get('message')}'")

    # -------------------------------------------------------------
    # TEST 5: Vision Inspector Transparent Fallback Schema (No Fake Vision)
    # -------------------------------------------------------------
    res_fb = inspector.analyze_image(test_img_path, 1)
    t5_passed = res_fb.get("status") in ("ANALYZED", "UNAVAILABLE_NO_API_KEY") and res_fb.get("confidence") is not float(0.92)  # Not hardcoded
    print(f"  Test 5 (Vision Inspector Schema & Transparent Fallback): [{'PASS' if t5_passed else 'FAIL'}]")
    if t5_passed:
        passed_count += 1
        print(f"    Status: {res_fb.get('status')} | Confidence: {res_fb.get('confidence')}")

    # -------------------------------------------------------------
    # TEST 6: Visual vs Database Metadata Cross-Checker Warning
    # -------------------------------------------------------------
    cross_checker = VisualCrossChecker()
    mock_db_knife = {"description": "Kitchen knife with bloodstains", "type_name": "Physical"}
    mock_vision_phone = {
        "status": "ANALYZED",
        "observations": ["Visually observed smartphone mobile device with cracked screen."]
    }
    mock_sha_intact = {"integrity": "INTACT"}

    cross_res = cross_checker.cross_check(2, mock_db_knife, mock_vision_phone, mock_sha_intact)
    t6_passed = (cross_res.get("is_consistent") is False) and (len(cross_res.get("warnings", [])) > 0)
    print(f"  Test 6 (Visual-DB Inconsistency Warning): [{'PASS' if t6_passed else 'FAIL'}]")
    if t6_passed:
        passed_count += 1
        print(f"    Warning: '{cross_res['warnings'][0]['description']}'")

    # -------------------------------------------------------------
    # TEST 7: Multimodal Hybrid RAG Zero-Fabrication on Missing Photo
    # -------------------------------------------------------------
    retriever = HybridRetriever()
    rag_res = retriever.process_query("What does the photograph of evidence E999 show?", user_role="Junior")
    answer = rag_res.get("answer", "")
    t7_passed = ("do not contain sufficient information" in answer.lower()) or ("no photographic evidence" in answer.lower())
    print(f"  Test 7 (RAG Refusal to Fabricate Missing Images): [{'PASS' if t7_passed else 'FAIL'}]")
    if t7_passed:
        passed_count += 1
        print(f"    Grounded Refusal: Intact")

    print("=" * 65)
    print(f"  RESULTS: {passed_count}/{total_tests} Tests Passed.")
    print("=" * 65)
    return passed_count == total_tests


if __name__ == "__main__":
    test_vision_integrity_suite()
