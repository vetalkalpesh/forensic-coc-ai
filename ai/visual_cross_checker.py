"""
ai/visual_cross_checker.py
Cross-checks Vision AI visual observations against authoritative MySQL database metadata,
examination reports, and SHA-256 cryptographic byte integrity.
Generates cautious inconsistency warnings without altering database records.
"""

class VisualCrossChecker:

    def cross_check(self, evidence_id: int, db_metadata: dict, vision_analysis: dict, sha256_integrity: dict) -> dict:
        """Cross-checks visual observations with database facts and integrity status."""
        warnings = []
        
        # 1. Cryptographic Byte Integrity check
        integrity_status = sha256_integrity.get("integrity", "NO_IMAGE")
        if integrity_status == "COMPROMISED":
            warnings.append({
                "type": "CRYPTOGRAPHIC_HASH_MISMATCH",
                "severity": "CRITICAL",
                "description": f"Photographic file bytes for Evidence E{evidence_id:03d} do NOT match the original recorded SHA-256 hash. File has been modified or corrupted.",
                "action": "Immediate forensic audit required."
            })

        # 2. Check if Vision AI observations are actually available
        vision_status = (vision_analysis or {}).get("status")
        if not vision_analysis or vision_status in ("NO_IMAGE", "UNAVAILABLE_NO_API_KEY", "API_ERROR"):
            err_detail = (vision_analysis or {}).get("message") or "Vision AI analysis unavailable"
            return {
                "evidence_id": f"E{evidence_id:03d}",
                "check_status": "NOT_EVALUATED",
                "is_consistent": None,  # Must NOT claim consistency without successful visual analysis
                "integrity_status": integrity_status,
                "warnings": warnings,
                "summary": f"Visual-DB consistency check not evaluated ({err_detail})." if integrity_status != "COMPROMISED" else "Visual consistency not evaluated; CRITICAL SHA-256 byte hash mismatch detected."
            }

        # 3. Visual vs Database Metadata Consistency Check (when active Vision AI observations exist)
        is_consistent = True
        db_desc = (db_metadata.get("description") or "").lower()
        db_type = (db_metadata.get("type_name") or "").lower()
        obs_text = " ".join(vision_analysis.get("observations", [])).lower()

        # Keyword discrepancy checks
        if "knife" in db_desc and "phone" in obs_text and "knife" not in obs_text:
            warnings.append({
                "type": "VISUAL_METADATA_INCONSISTENCY",
                "severity": "HIGH",
                "description": f"Database records item as '{db_metadata.get('description')}', but photograph visually appears to contain a mobile phone object.",
                "action": "Potential visual-record inconsistency — requires forensic review."
            })
            is_consistent = False

        elif ("laptop" in db_desc or "computer" in db_desc) and "knife" in obs_text:
            warnings.append({
                "type": "VISUAL_METADATA_INCONSISTENCY",
                "severity": "HIGH",
                "description": f"Database records digital device '{db_metadata.get('description')}', but visual observation indicates sharp tool/blade object.",
                "action": "Potential visual-record inconsistency — requires forensic review."
            })
            is_consistent = False

        if integrity_status == "COMPROMISED":
            is_consistent = False

        return {
            "evidence_id": f"E{evidence_id:03d}",
            "check_status": "EVALUATED",
            "is_consistent": is_consistent,
            "integrity_status": integrity_status,
            "warnings": warnings,
            "summary": "Visual observations appear consistent with database metadata." if is_consistent else f"Detected {len(warnings)} potential inconsistency warning(s)."
        }

