"""
merge_results.py

Merges baseline and experiment JSON results into a single file
following the CONTRIBUTING.md format.

Usage:
    python merge_results.py

Expected input files in /workspace/results/:
    result_baseline_python-dotenv_str-count-newline-advance.json
    result_experiment_python-dotenv_str-count-newline-advance.json

Output:
    result_python-dotenv_str-count-newline-advance.json
"""

import json
import os

RESULTS_DIR = "results/python-dotenv"
BASELINE_FILE = os.path.join(RESULTS_DIR, "result_baseline_python-dotenv_str-count-newline-advance.json")
EXPERIMENT_FILE = os.path.join(RESULTS_DIR, "result_experiment_python-dotenv_str-count-newline-advance.json")
OUTPUT_FILE = os.path.join(RESULTS_DIR, "result_python-dotenv_str-count-newline-advance.json")


def load_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def main():
    print("Loading baseline results...")
    baseline_data = load_json(BASELINE_FILE)

    print("Loading experiment results...")
    experiment_data = load_json(EXPERIMENT_FILE)

    baseline = baseline_data["baseline"]
    optimized = experiment_data["optimized"]

    improvement_pct = round(
        ((baseline["mean_ms"] - optimized["mean_ms"]) / baseline["mean_ms"]) * 100, 2
    )

    improvement_confirmed = (
        baseline["mean_ms"] - optimized["mean_ms"]
    ) > baseline["std_ms"]

    result = {
        "experiment": "str-count-newline-advance",
        "project": "python-dotenv",
        "baseline": baseline,
        "optimized": optimized,
        "improvement_pct": improvement_pct,
        "improvement_confirmed": improvement_confirmed,
        "config": {
            "env_vars": 24999,
            "warmup_runs": 5,
        },
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()


