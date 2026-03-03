import argparse
import json
import os
import random
import shutil
import statistics
import sys
import tempfile
import time

import whoosh.index as index
from whoosh.fields import ID, TEXT, Schema
from whoosh.query import And, Term


def parse_args():
    parser = argparse.ArgumentParser(
        description="Experiment: AND-intersection performance with Skip Lists"
    )
    parser.add_argument("--docs", type=int, default=500_000)
    parser.add_argument("--high-freq", type=int, default=100_000)
    parser.add_argument("--low-freq", type=int, default=1_000)
    parser.add_argument("--query-pairs", type=int, default=100)
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument(
        "--output",
        type=str,
        default="/results/result_whoosh-reloaded_skip-lists.json",
    )
    parser.add_argument("--baseline", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _detect_skip_list() -> bool:
    try:
        from whoosh.matching.mcore import SkipListMatcher
        return hasattr(SkipListMatcher, "_skiplist") or hasattr(SkipListMatcher, "skip_to")
    except ImportError:
        return False


_HIGH_FREQ_TOKEN = "xhighfreqtoken"
_LOW_FREQ_TOKEN = "xlowfreqtoken"
_FILLER_PREFIX = "xfill"


def _unique_filler(i: int) -> str:
    return f"{_FILLER_PREFIX}{i:08d}"


def build_index(
    index_dir: str,
    doc_count: int,
    high_freq_count: int,
    low_freq_count: int,
    rng: random.Random,
) -> tuple:
    schema = Schema(id=ID(stored=True), content=TEXT(stored=False))
    ix = index.create_in(index_dir, schema)
    writer = ix.writer()

    low_freq_ids = set(rng.sample(range(high_freq_count), min(low_freq_count, high_freq_count)))

    for i in range(doc_count):
        tokens = [_unique_filler(i)]
        if i < high_freq_count:
            tokens.append(_HIGH_FREQ_TOKEN)
        if i in low_freq_ids:
            tokens.append(_LOW_FREQ_TOKEN)
        writer.add_document(id=str(i), content=" ".join(tokens))

    writer.commit()
    return set(range(high_freq_count)), low_freq_ids


def run_benchmark(ix, query_pairs: list) -> float:
    searcher = ix.searcher()

    start = time.perf_counter()
    for high_term, low_term in query_pairs:
        q = And([Term("content", high_term), Term("content", low_term)])
        _ = len(searcher.search(q, limit=None))
    end = time.perf_counter()

    searcher.close()
    return (end - start) * 1_000.0


def main():
    args = parse_args()
    rng = random.Random(args.seed)

    if not _detect_skip_list():
        print("[WARNING] Skip List not detected in IntersectionMatcher; benchmarking unoptimized build.")

    index_dir = tempfile.mkdtemp(prefix="whoosh_skiplist_experiment_")
    try:
        build_index(index_dir, args.docs, args.high_freq, args.low_freq, rng)
        ix = index.open_dir(index_dir)
        query_pairs = [(_HIGH_FREQ_TOKEN, _LOW_FREQ_TOKEN)] * args.query_pairs

        run_benchmark(ix, query_pairs)  # warm-up

        timings_ms = [run_benchmark(ix, query_pairs) for _ in range(args.runs)]
        ix.close()
    finally:
        shutil.rmtree(index_dir, ignore_errors=True)

    mean_ms = statistics.mean(timings_ms)
    std_ms = statistics.stdev(timings_ms)

    baseline_mean = None
    baseline_std = None
    baseline_runs = None
    improvement_pct = None
    improvement_confirmed = False

    if args.baseline and os.path.isfile(args.baseline):
        with open(args.baseline, encoding="utf-8") as fh:
            bl = json.load(fh)
        baseline_mean = bl.get("baseline", {}).get("mean_ms")
        baseline_std = bl.get("baseline", {}).get("std_ms")
        baseline_runs = bl.get("baseline", {}).get("runs")

        if baseline_mean and baseline_mean > 0:
            improvement_pct = ((baseline_mean - mean_ms) / baseline_mean) * 100.0
            if baseline_std is not None:
                improvement_confirmed = mean_ms < (baseline_mean - baseline_std)

    result = {
        "experiment": "skip-lists-boolean-intersection",
        "project": "whoosh-reloaded",
        "variant": "optimized",
        "baseline": {
            "mean_ms": baseline_mean,
            "std_ms": baseline_std,
            "runs": baseline_runs,
        },
        "optimized": {
            "mean_ms": round(mean_ms, 4),
            "std_ms": round(std_ms, 4),
            "runs": args.runs,
        },
        "improvement_pct": round(improvement_pct, 2) if improvement_pct is not None else None,
        "improvement_confirmed": improvement_confirmed,
        "config": {
            "docs": args.docs,
            "high_freq_count": args.high_freq,
            "low_freq_count": args.low_freq,
            "query_pairs_per_run": args.query_pairs,
            "seed": args.seed,
        },
    }

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    print(f"experiment saved to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
