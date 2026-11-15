from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict, Iterable, List


def build_call_graph(spans: Iterable[dict]) -> Dict[str, set]:
    spans = list(spans)
    by_id = {s["span_id"]: s for s in spans}
    graph: Dict[str, set] = defaultdict(set)
    for s in spans:
        graph.setdefault(s["service"], set())
        parent = by_id.get(s.get("parent_id"))
        if parent and parent["service"] != s["service"]:
            graph[parent["service"]].add(s["service"])
    return dict(graph)


def zscore_anomaly(series: List[float], threshold: float = 3.0) -> float:
    if len(series) < 3:
        raise ValueError("Нужно минимум 3 точки временного ряда")
    history, last = series[:-1], series[-1]
    mean = sum(history) / len(history)
    var = sum((x - mean) ** 2 for x in history) / len(history)
    std = math.sqrt(var)
    if std == 0:
        return 0.0 if last == mean else math.inf
    return (last - mean) / std


def detect_anomalies(metrics: Dict[str, List[float]], threshold: float = 3.0) -> Dict[str, float]:
    result = {}
    for service, series in metrics.items():
        z = zscore_anomaly(series, threshold)
        if abs(z) >= threshold:
            result[service] = z
    return result


def pearson(x: List[float], y: List[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Ряды должны быть одной длины (>= 2)")
    mx, my = sum(x) / len(x), sum(y) / len(y)
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    if sx == 0 or sy == 0:
        return 0.0
    return cov / (sx * sy)


def _downstream(graph: Dict[str, set], node: str) -> set:
    seen, stack = set(), list(graph.get(node, ()))
    while stack:
        n = stack.pop()
        if n not in seen:
            seen.add(n)
            stack.extend(graph.get(n, ()))
    return seen


def analyze(spans: Iterable[dict], metrics: Dict[str, List[float]],
            symptom: str, threshold: float = 3.0) -> List[dict]:
    graph = build_call_graph(spans)
    anomalies = detect_anomalies(metrics, threshold)
    symptom_series = metrics[symptom]

    candidates = []
    for service, z in anomalies.items():
        has_anomalous_child = bool(_downstream(graph, service) & anomalies.keys())
        corr = abs(pearson(metrics[service], symptom_series))
        score = corr * (0.3 if has_anomalous_child else 1.0)
        candidates.append({
            "service": service,
            "zscore": round(z, 2) if math.isfinite(z) else z,
            "correlation": round(corr, 3),
            "score": round(score, 3),
        })
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates
