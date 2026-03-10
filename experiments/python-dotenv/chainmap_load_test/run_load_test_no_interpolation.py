
import gc
import json
import math
import os
import statistics
import sys
import time
import glob


import dotenv

TOTAL_RUNS = 50
WARMUP_RUNS = 10
INPUT_DIR = os.path.join(os.path.dirname(__file__), "without_interpolation")


def count_lines(filepath: str) -> int:
    with open(filepath, "r") as f:
        return sum(1 for line in f if line.strip())


def clean_env(filepath: str) -> None:
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key = line.split("=", 1)[0]
                os.environ.pop(key, None)


def benchmark_file(filepath: str) -> dict:
    num_lines = count_lines(filepath)
    env_size = len(os.environ)

    times = []
    for i in range(TOTAL_RUNS):
        clean_env(filepath)

        gc.disable()
        start = time.perf_counter_ns()
        dotenv.load_dotenv(dotenv_path=filepath)
        end = time.perf_counter_ns()
        gc.enable()

        elapsed_ms = (end - start) / 1_000_000
        times.append(elapsed_ms)

        time.sleep(0.01)

    measured = times[WARMUP_RUNS:]
    median_ms = statistics.median(measured)
    stdev_ms = statistics.stdev(measured) if len(measured) > 1 else 0.0

    clean_env(filepath)

    return {
        "number_of_variables_environ": env_size,
        "time_to_load_ms": round(median_ms, 4),
        "stdev_ms": round(stdev_ms, 4),
        "number_of_variables_env": num_lines,
    }

def main():
    env_files = sorted(
        glob.glob(os.path.join(INPUT_DIR, "*.env")),
        key=lambda f: count_lines(f),
    )
    results = []
    for filepath in env_files:
        result = benchmark_file(filepath)
        results.append(result)

    output_path = os.path.join(os.path.dirname(__file__),"..","..","results","results-no-interpolated.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


main()
