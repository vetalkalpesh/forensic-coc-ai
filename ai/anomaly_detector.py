import math
from typing import List, Dict, Any, Optional

# Default configurable threshold for suspicious movement speed (km/h)
DEFAULT_MAX_PLAUSIBLE_SPEED_KMH = 120.0

def haversine(lat1: Optional[float], lon1: Optional[float], lat2: Optional[float], lon2: Optional[float]) -> float:
    """Calculate the great circle distance in kilometers between two points on Earth."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0.0
    
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    except (ValueError, TypeError):
        return 0.0

    R = 6371.0  # Radius of Earth in kilometers
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2.0) ** 2 + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dLon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def detect_custody_anomalies(
    transfers: List[Dict[str, Any]],
    evidence_id: Optional[Any] = None,
    max_speed_threshold_kmh: float = DEFAULT_MAX_PLAUSIBLE_SPEED_KMH
) -> Dict[str, Any]:
    """
    Analyzes custody transfers for an evidence item for temporal and geospatial anomalies.
    Expects transfers ordered by log_id (custody log sequence) or transfer_datetime.
    """
    if not transfers:
        return {
            "evidence_id": evidence_id,
            "status": "NO_DATA",
            "anomalies": [],
            "anomaly_count": 0
        }

    # Sort transfers by log_id if present, to preserve original custody sequence
    def get_log_key(t):
        lid = t.get("log_id")
        if lid is not None:
            return lid
        dt = t.get("transfer_datetime")
        return str(dt) if dt is not None else ""

    sorted_transfers = sorted(transfers, key=get_log_key)
    anomalies = []

    for i in range(len(sorted_transfers)):
        curr = sorted_transfers[i]
        curr_log_id = curr.get("log_id")
        from_name = curr.get("from_dept_name") or "Origin Department"
        to_name = curr.get("to_dept_name") or "Destination Department"

        from_lat, from_lon = curr.get("from_lat"), curr.get("from_lon")
        to_lat, to_lon = curr.get("to_lat"), curr.get("to_lon")

        # Parse current transfer timestamp
        dt_curr = curr.get("transfer_datetime")
        if not dt_curr:
            continue

        if i > 0:
            prev = sorted_transfers[i - 1]
            prev_log_id = prev.get("log_id")
            dt_prev = prev.get("transfer_datetime")
            
            if dt_prev:
                try:
                    if hasattr(dt_curr, "timestamp") and hasattr(dt_prev, "timestamp"):
                        elapsed_seconds = dt_curr.timestamp() - dt_prev.timestamp()
                    else:
                        from datetime import datetime
                        d1 = datetime.fromisoformat(str(dt_curr))
                        d2 = datetime.fromisoformat(str(dt_prev))
                        elapsed_seconds = (d1 - d2).total_seconds()
                except Exception:
                    elapsed_seconds = None

                if elapsed_seconds is not None:
                    elapsed_hours = elapsed_seconds / 3600.0
                    elapsed_minutes = elapsed_seconds / 60.0

                    # 1. Temporal Ordering Issue (negative elapsed time in log sequence)
                    if elapsed_seconds < 0:
                        anomalies.append({
                            "type": "TEMPORAL_ORDERING_INCONSISTENCY",
                            "evidence_id": evidence_id or curr.get("evidence_id"),
                            "log_id": curr_log_id,
                            "previous_log_id": prev_log_id,
                            "from_location": from_name,
                            "to_location": to_name,
                            "elapsed_minutes": round(elapsed_minutes, 2),
                            "severity": "HIGH",
                            "explanation": f"Potential temporal inconsistency detected: Transfer log #{curr_log_id} has timestamp earlier than preceding transfer log #{prev_log_id} ({round(abs(elapsed_minutes), 1)} min difference). This is an anomaly requiring review and does not by itself establish fraud or misconduct."
                        })
                        continue

                    # 2. Movement across distance in transfer
                    if from_lat is not None and from_lon is not None and to_lat is not None and to_lon is not None:
                        dist_km = haversine(from_lat, from_lon, to_lat, to_lon)
                        if dist_km > 0.5:  # Significant physical distance (> 500m)
                            if elapsed_hours <= 0.0001:  # Virtually zero time elapsed
                                anomalies.append({
                                    "type": "IMPOSSIBLE_INSTANTANEOUS_MOVEMENT",
                                    "evidence_id": evidence_id or curr.get("evidence_id"),
                                    "log_id": curr_log_id,
                                    "previous_log_id": prev_log_id,
                                    "from_location": from_name,
                                    "to_location": to_name,
                                    "distance_km": round(dist_km, 2),
                                    "elapsed_minutes": round(elapsed_minutes, 2),
                                    "implied_speed_kmh": "INFINITE",
                                    "threshold_kmh": max_speed_threshold_kmh,
                                    "severity": "HIGH",
                                    "explanation": f"Deterministic temporal/geospatial anomaly detected: Evidence recorded moving {round(dist_km, 2)} km between {from_name} and {to_name} with 0 elapsed time. This is an anomaly requiring review and does not by itself establish fraud or misconduct."
                                })
                            else:
                                implied_speed = dist_km / elapsed_hours
                                if implied_speed > max_speed_threshold_kmh:
                                    anomalies.append({
                                        "type": "IMPOSSIBLE_TRAVEL_SPEED",
                                        "evidence_id": evidence_id or curr.get("evidence_id"),
                                        "log_id": curr_log_id,
                                        "previous_log_id": prev_log_id,
                                        "from_location": from_name,
                                        "to_location": to_name,
                                        "distance_km": round(dist_km, 2),
                                        "elapsed_minutes": round(elapsed_minutes, 2),
                                        "implied_speed_kmh": round(implied_speed, 2),
                                        "threshold_kmh": max_speed_threshold_kmh,
                                        "severity": "HIGH" if implied_speed > (max_speed_threshold_kmh * 2) else "MEDIUM",
                                        "explanation": f"Deterministic temporal/geospatial anomaly detected: Recorded transfer from {from_name} to {to_name} ({round(dist_km, 2)} km in {round(elapsed_minutes, 1)} mins) implies a travel speed of {round(implied_speed, 1)} km/h, exceeding configured threshold of {max_speed_threshold_kmh} km/h. This is an anomaly requiring review and does not by itself establish fraud or misconduct."
                                    })

    return {
        "evidence_id": evidence_id,
        "status": "ANALYZED",
        "transfers_analyzed": len(sorted_transfers),
        "anomalies": anomalies,
        "anomaly_count": len(anomalies)
    }
