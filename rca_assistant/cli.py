import argparse
import json
import sys

from .analyzer import analyze


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="RCA Assistant (lite)")
    parser.add_argument("incident", help="JSON-файл с полями spans, metrics, symptom")
    parser.add_argument("--threshold", type=float, default=3.0, help="порог z-score")
    args = parser.parse_args(argv)

    with open(args.incident, encoding="utf-8") as f:
        data = json.load(f)

    ranking = analyze(data["spans"], data["metrics"], data["symptom"], args.threshold)
    if not ranking:
        print("Аномалий не обнаружено")
        return 0

    print("Кандидаты в корневую причину:")
    for i, c in enumerate(ranking, 1):
        print(f"{i}. {c['service']:<10} score={c['score']:<6} "
              f"corr={c['correlation']:<6} z={c['zscore']}")
    print(f"\nВероятная корневая причина: {ranking[0]['service']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
