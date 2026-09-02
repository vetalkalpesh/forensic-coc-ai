import sys
import os
from datetime import datetime
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.anomaly_detector import haversine, detect_custody_anomalies, DEFAULT_MAX_PLAUSIBLE_SPEED_KMH


def test_haversine_correctness():
    """Verify Haversine formula distance calculation accuracy."""
    # Pune Crime Branch (18.5314, 73.8446) to State FSL Kalina Mumbai (19.0734, 72.8591)
    dist = haversine(18.5314, 73.8446, 19.0734, 72.8591)
    assert round(dist, 1) == 120.0  # Approx 120 km great circle distance

    # Same location should yield 0 distance
    assert haversine(18.5314, 73.8446, 18.5314, 73.8446) == 0.0


def test_normal_movement_no_anomaly():
    """Normal realistic custody movement should yield zero anomalies."""
    t1 = {
        'log_id': 101, 'evidence_id': 1,
        'transfer_datetime': datetime(2026, 1, 1, 9, 0),
        'from_dept_name': 'Pune Crime Branch', 'to_dept_name': 'Central Evidence Storage',
        'from_lat': 18.5314, 'from_lon': 73.8446, 'to_lat': 18.5314, 'to_lon': 73.8446
    }
    t2 = {
        'log_id': 102, 'evidence_id': 1,
        'transfer_datetime': datetime(2026, 1, 1, 12, 0),  # 3 hours later for 120km drive
        'from_dept_name': 'Central Evidence Storage', 'to_dept_name': 'State Forensic Science Lab',
        'from_lat': 18.5314, 'from_lon': 73.8446, 'to_lat': 19.0734, 'to_lon': 72.8591
    }

    result = detect_custody_anomalies([t1, t2], evidence_id=1)
    assert result["status"] == "ANALYZED"
    assert result["anomaly_count"] == 0
    assert len(result["anomalies"]) == 0


def test_impossible_travel_speed():
    """Impossibly fast travel speed (120 km in 5 mins = 1439 km/h) must trigger an anomaly."""
    t1 = {
        'log_id': 101, 'evidence_id': 1,
        'transfer_datetime': datetime(2026, 1, 1, 10, 0),
        'from_dept_name': 'Pune Crime Branch', 'to_dept_name': 'Pune Crime Branch',
        'from_lat': 18.5314, 'from_lon': 73.8446, 'to_lat': 18.5314, 'to_lon': 73.8446
    }
    t2 = {
        'log_id': 102, 'evidence_id': 1,
        'transfer_datetime': datetime(2026, 1, 1, 10, 5),  # 5 minutes later
        'from_dept_name': 'Pune Crime Branch', 'to_dept_name': 'State Forensic Science Lab',
        'from_lat': 18.5314, 'from_lon': 73.8446, 'to_lat': 19.0734, 'to_lon': 72.8591
    }

    result = detect_custody_anomalies([t1, t2], evidence_id=1)
    assert result["anomaly_count"] == 1
    anom = result["anomalies"][0]
    assert anom["type"] == "IMPOSSIBLE_TRAVEL_SPEED"
    assert anom["log_id"] == 102
    assert anom["implied_speed_kmh"] > 1000.0


def test_negative_elapsed_time():
    """Transfer logged earlier than preceding transfer must trigger a temporal inconsistency anomaly."""
    t1 = {
        'log_id': 101, 'evidence_id': 1,
        'transfer_datetime': datetime(2026, 1, 1, 12, 0),
        'from_dept_name': 'Pune Crime Branch', 'to_dept_name': 'Pune Crime Branch',
        'from_lat': 18.5314, 'from_lon': 73.8446, 'to_lat': 18.5314, 'to_lon': 73.8446
    }
    t2 = {
        'log_id': 102, 'evidence_id': 1,
        'transfer_datetime': datetime(2026, 1, 1, 11, 0),  # 1 hour earlier
        'from_dept_name': 'Pune Crime Branch', 'to_dept_name': 'State Forensic Science Lab',
        'from_lat': 18.5314, 'from_lon': 73.8446, 'to_lat': 19.0734, 'to_lon': 72.8591
    }

    result = detect_custody_anomalies([t1, t2], evidence_id=1)
    assert result["anomaly_count"] == 1
    anom = result["anomalies"][0]
    assert anom["type"] == "TEMPORAL_ORDERING_INCONSISTENCY"


def test_missing_coordinates_handled_safely():
    """Missing latitude/longitude should be handled safely without throwing errors or fabricating data."""
    t1 = {
        'log_id': 101, 'evidence_id': 1,
        'transfer_datetime': datetime(2026, 1, 1, 10, 0),
        'from_dept_name': 'Unknown Dept', 'to_dept_name': 'Unknown Dept',
        'from_lat': None, 'from_lon': None, 'to_lat': None, 'to_lon': None
    }
    t2 = {
        'log_id': 102, 'evidence_id': 1,
        'transfer_datetime': datetime(2026, 1, 1, 10, 5),
        'from_dept_name': 'Unknown Dept 2', 'to_dept_name': 'Unknown Dept 2',
        'from_lat': None, 'from_lon': None, 'to_lat': None, 'to_lon': None
    }

    result = detect_custody_anomalies([t1, t2], evidence_id=1)
    assert result["status"] == "ANALYZED"
    assert result["anomaly_count"] == 0


def test_missing_timestamps_handled_safely():
    """Missing transfer_datetime should be handled safely without error."""
    t1 = {'log_id': 101, 'evidence_id': 1, 'transfer_datetime': None}
    t2 = {'log_id': 102, 'evidence_id': 1, 'transfer_datetime': None}

    result = detect_custody_anomalies([t1, t2], evidence_id=1)
    assert result["anomaly_count"] == 0


def test_configurable_threshold_behavior():
    """Configurable max speed threshold should alter anomaly detection sensitivity."""
    t1 = {
        'log_id': 101, 'evidence_id': 1,
        'transfer_datetime': datetime(2026, 1, 1, 10, 0),
        'from_dept_name': 'Pune', 'to_dept_name': 'Pune',
        'from_lat': 18.5314, 'from_lon': 73.8446, 'to_lat': 18.5314, 'to_lon': 73.8446
    }
    t2 = {
        'log_id': 102, 'evidence_id': 1,
        'transfer_datetime': datetime(2026, 1, 1, 11, 0),  # 1 hour for 120km -> 120 km/h
        'from_dept_name': 'Pune', 'to_dept_name': 'Mumbai',
        'from_lat': 18.5314, 'from_lon': 73.8446, 'to_lat': 19.0734, 'to_lon': 72.8591
    }

    # At threshold 130 km/h, 120 km/h is NOT an anomaly
    res_high = detect_custody_anomalies([t1, t2], evidence_id=1, max_speed_threshold_kmh=130.0)
    assert res_high["anomaly_count"] == 0

    # At threshold 80 km/h, 120 km/h IS an anomaly
    res_low = detect_custody_anomalies([t1, t2], evidence_id=1, max_speed_threshold_kmh=80.0)
    assert res_low["anomaly_count"] == 1


def test_forensic_wording_neutrality():
    """Verify anomaly explanations contain proper neutral forensic wording and do not claim fraud."""
    t1 = {
        'log_id': 101, 'evidence_id': 1,
        'transfer_datetime': datetime(2026, 1, 1, 10, 0),
        'from_dept_name': 'Pune', 'to_dept_name': 'Pune',
        'from_lat': 18.5314, 'from_lon': 73.8446, 'to_lat': 18.5314, 'to_lon': 73.8446
    }
    t2 = {
        'log_id': 102, 'evidence_id': 1,
        'transfer_datetime': datetime(2026, 1, 1, 10, 5),
        'from_dept_name': 'Pune', 'to_dept_name': 'Mumbai',
        'from_lat': 18.5314, 'from_lon': 73.8446, 'to_lat': 19.0734, 'to_lon': 72.8591
    }

    result = detect_custody_anomalies([t1, t2], evidence_id=1)
    explanation = result["anomalies"][0]["explanation"]
    
    assert "does not by itself establish fraud or misconduct" in explanation
    assert "Officer committed fraud" not in explanation
    assert "forged" not in explanation
