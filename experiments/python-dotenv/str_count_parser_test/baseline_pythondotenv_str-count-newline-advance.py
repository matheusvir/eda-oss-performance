import json
import os
import statistics
import time

from dotenv import dotenv_values

RESULTS_DIR = "/workspace/results"
ENV_FILE = "/tmp/test_baseline.env"
WARMUP_RUNS = 5
RUNS = 40


def generate_env_file(path: str, num_groups: int = 8333) -> None:
    with open(path, "w") as f:
        for i in range(num_groups):
            f.write(f"BASE_{i}=/home/user_{i}\n")
            f.write(f"PATH_{i}=${{BASE_{i}}}/projetos\n")
            f.write(f"FULL_{i}=${{PATH_{i}}}/app\n")


def remove_outliers(times: list) -> list:
    sorted_times = sorted(times)
    n = len(sorted_times)
    q1 = sorted_times[n // 4]
    q3 = sorted_times[(3 * n) // 4]
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    filtered = [t for t in times if lower <= t <= upper]
    return filtered


def measure(env_file: str, runs: int = RUNS) -> list:
    for _ in range(WARMUP_RUNS):
        dotenv_values(env_file)

    times = []
    for _ in range(runs):
        start = time.perf_counter()
        dotenv_values(env_file)
        end = time.perf_counter()
        times.append((end - start) * 1000)
    return times


def main():
    generate_env_file(ENV_FILE)

    times = measure(ENV_FILE)

    filtered = remove_outliers(times)

    mean = statistics.mean(filtered)
    std = statistics.stdev(filtered)

    result = {
        "experiment": "str-count-newline-advance",
        "project": "python-dotenv",
        "variant": "baseline",
        "baseline": {
            "mean_ms": round(mean, 4),
            "std_ms": round(std, 4),
            "runs": len(filtered),
        },
    }

    os.makedirs(RESULTS_DIR, exist_ok=True)
    output = os.path.join(RESULTS_DIR, "result_baseline_python-dotenv_str-count-newline-advance.json")
    with open(output, "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()
