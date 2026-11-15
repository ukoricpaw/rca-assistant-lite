import json
import math
from pathlib import Path

import pytest

from rca_assistant import analyze, build_call_graph, detect_anomalies, pearson, zscore_anomaly

DATA = Path(__file__).resolve().parent.parent / "data" / "sample_incident.json"


def test_build_call_graph_from_spans():
    spans = [
        {"span_id": "a", "parent_id": None, "service": "frontend"},
        {"span_id": "b", "parent_id": "a", "service": "orders"},
        {"span_id": "c", "parent_id": "b", "service": "db"},
    ]
    graph = build_call_graph(spans)
    assert graph["frontend"] == {"orders"}
    assert graph["orders"] == {"db"}
    assert graph["db"] == set()


def test_zscore_detects_spike_and_ignores_normal_series():
    assert zscore_anomaly([10, 11, 9, 10, 11, 9, 50]) > 3
    assert abs(zscore_anomaly([10, 11, 9, 10, 11, 9, 10])) < 3
    anomalies = detect_anomalies({"a": [1, 2, 1, 2, 30], "b": [1, 2, 1, 2, 1]})
    assert set(anomalies) == {"a"}


def test_zscore_requires_enough_points():
    with pytest.raises(ValueError):
        zscore_anomaly([1, 2])

def test_pearson_correlation_values():
    assert pearson([1, 2, 3, 4], [2, 4, 6, 8]) == pytest.approx(1.0)
    assert pearson([1, 2, 3, 4], [8, 6, 4, 2]) == pytest.approx(-1.0)
    assert pearson([1, 1, 1], [1, 2, 3]) == 0.0

def test_analyze_finds_root_cause_on_sample_incident():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    ranking = analyze(data["spans"], data["metrics"], data["symptom"])
    assert ranking[0]["service"] == "db"
    assert "auth" not in {c["service"] for c in ranking}
    assert all(math.isfinite(c["score"]) for c in ranking)
