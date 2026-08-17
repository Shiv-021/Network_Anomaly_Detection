"""
backend/app/services/stats_service.py
========================================
Process-lifetime prediction counters and SSE payload builder.

Public API
----------
    record_prediction(is_anomaly)  — call after every successful inference
    stats_payload()                — snapshot dict for /api/stats and /api/events
    reset()                        — reset counters (useful in tests)
"""
import time
import collections

_stats: dict = {
    "total":      0,
    "anomalies":  0,
    "normal":     0,
    "start_time": time.time(),
}
# Sliding window of the last 600 prediction timestamps (≈ 10-min window at 1/s)
_recent_ts: collections.deque = collections.deque(maxlen=600)


def record_prediction(is_anomaly: bool) -> None:
    """Increment counters. Thread-safe for CPython (GIL-protected dicts)."""
    _stats["total"] += 1
    if is_anomaly:
        _stats["anomalies"] += 1
    else:
        _stats["normal"] += 1
    _recent_ts.append(time.time())


def stats_payload() -> dict:
    """Return a JSON-serialisable snapshot of current counters."""
    now    = time.time()
    recent = sum(1 for t in _recent_ts if now - t < 60)
    return {
        "total":      _stats["total"],
        "anomalies":  _stats["anomalies"],
        "normal":     _stats["normal"],
        "uptime":     int(now - _stats["start_time"]),
        "per_minute": recent,
    }


def reset() -> None:
    """Reset all counters — intended for unit-test isolation."""
    _stats.update({"total": 0, "anomalies": 0, "normal": 0, "start_time": time.time()})
    _recent_ts.clear()
