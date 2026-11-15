# RCA Assistant (lite)

A simplified prototype of an AI assistant that automatically determines the root cause
of incidents in a microservice architecture by correlating distributed traces and metrics.

Algorithm:

1. A service call graph is built from the traces (spans).
2. Anomalies are detected in each service's metrics (latency/errors) using the z-score of the last point.
3. For anomalous services, the Pearson correlation with the symptom service's metric is computed.
4. A service that has anomalous dependencies further down the graph is treated as a "victim" and
   penalized; the "deepest" anomalous service rises to the top of the ranking.

## Structure

```
rca-assistant/
├── rca_assistant/
│   ├── analyzer.py        # call graph, z-score, correlation, ranking
│   └── cli.py             # command-line entry point
├── data/sample_incident.json  # reference incident (root cause: db)
├── tests/test_analyzer.py     # unit tests (pytest)
├── .github/workflows/ci.yml   # CI on GitHub Actions
├── docs/                      # project report
├── requirements.txt           # pinned dependency versions
└── pytest.ini
```

## Reproducibility

### Requirements

- Python 3.10–3.12 (tested in CI on 3.10, 3.11, 3.12)
- Git
- The code itself has no third-party dependencies; `requirements.txt` contains only testing
  tools with **pinned versions** (`pytest==8.3.3`, `flake8==7.1.1`).

### Steps

```bash
# 1. Clone the repository
git clone <repository-URL> rca-assistant
cd rca-assistant

# 2. Create an isolated environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the tests
pytest -v

# 5. Analyze the reference incident
python -m rca_assistant.cli data/sample_incident.json
```

### Expected result

- `pytest`: **5 passed**.
- The CLI prints a ranking of candidates and the line
  `Вероятная корневая причина: db` ("Probable root cause: db").

The result is deterministic: the algorithm uses no randomness, the input data is stored
in the repository (`data/sample_incident.json`), and dependency versions are pinned.

### Your own incident

Prepare a JSON file in the same format:

```json
{
  "symptom": "frontend",
  "spans":   [{"span_id": "1", "parent_id": null, "service": "frontend"}, ...],
  "metrics": {"frontend": [100, 101, ...], "db": [10, 11, ...]}
}
```

and run `python -m rca_assistant.cli path/to/incident.json --threshold 3`.

## CI

The `.github/workflows/ci.yml` workflow runs on every `push` to `main` and on every
pull request. Steps: Python setup (3.10/3.11/3.12 matrix) → dependency installation →
`flake8` style check → `pytest` unit tests → CLI smoke run on the reference data.
