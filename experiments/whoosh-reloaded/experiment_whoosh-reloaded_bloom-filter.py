"""Experiment benchmark for negative term lookups WITH Bloom filter.

Indexes 500k documents and queries for 1000 absent terms per run.
This script runs against whoosh with the bloom filter optimization,
which short-circuits absent-term lookups via an in-memory bit array
before hitting the on-disk hash table.

Methodology:
  - 50 runs total
  - Discard first 10 (warmup) and last 10 (cooldown)
  - Use middle 30 runs for statistics
  - GC disabled during measurement
  - Each run performs 1000 lookups of nonexistent terms
"""

import argparse
import gc
import json
import os
import shutil
import statistics
import sys
import tempfile
import time

import whoosh.index as index
from whoosh.fields import ID, TEXT, Schema
from whoosh.query import Term

TOTAL_RUNS = 50
DISCARD = 10


def parse_args():
    parser = argparse.ArgumentParser(
        description="Experiment: negative term lookup performance with Bloom filter"
    )
    parser.add_argument("--docs", type=int, default=500_000)
    parser.add_argument("--absent-queries", type=int, default=1_000)
    parser.add_argument("--total-runs", type=int, default=TOTAL_RUNS)
    parser.add_argument("--discard", type=int, default=DISCARD)
    parser.add_argument(
        "--output",
        type=str,
        default="/results/result_whoosh-reloaded_bloom-filter.json",
    )
    parser.add_argument("--baseline", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _detect_bloom_filter() -> bool:
    """Check whether the bloom filter optimization is available."""
    try:
        from whoosh.support.bloom import BloomFilter  # noqa: F401
        from whoosh.codec.whoosh3 import W3Codec
        return hasattr(W3Codec, "BLOOM_EXT")
    except ImportError:
        return False


_DOC_PREFIX = "existingterm"
_ABSENT_PREFIX = "absentterm"


def _existing_token(i: int) -> str:
    """Generate a token that will exist in the index."""
    return f"{_DOC_PREFIX}{i:08d}"


def _absent_token(i: int) -> str:
    """Generate a token guaranteed to NOT exist in the index."""
    return f"{_ABSENT_PREFIX}{i:08d}"


def build_index(index_dir: str, doc_count: int) -> None:
    """Build a whoosh index with bloom filter enabled (default).

    The bloom filter is automatically created when the codec supports it.
    A .blm file will be written alongside the regular index segments.

    :param index_dir: Directory to create the index in.
    :param doc_count: Number of documents to index.
    """
    schema = Schema(id=ID(stored=True), content=TEXT(stored=False))
    ix = index.create_in(index_dir, schema)
    writer = ix.writer()

    for i in range(doc_count):
        token = _existing_token(i)
        writer.add_document(id=str(i), content=token)

    writer.commit()


def generate_absent_queries(count: int, doc_count: int) -> list:
    """Generate a list of query strings for terms that do NOT exist.

    Uses a separate prefix to guarantee no overlap with indexed tokens.

    :param count: Number of absent queries to generate.
    :param doc_count: Total docs in index (used for offset).
    :return: List of absent term strings.
    """
    return [_absent_token(doc_count + i) for i in range(count)]


def run_benchmark(ix, absent_terms: list) -> float:
    """Run a single benchmark iteration: search for all absent terms.

    :param ix: Opened whoosh index.
    :param absent_terms: List of term strings known to not exist.
    :return: Total elapsed time in milliseconds.
    """
    searcher = ix.searcher()

    gc.collect()
    gc.disable()
    start = time.perf_counter()
    for term_text in absent_terms:
        q = Term("content", term_text)
        _ = searcher.search(q, limit=1)
    end = time.perf_counter()
    gc.enable()

    searcher.close()
    return (end - start) * 1_000.0


def main():
    args = parse_args()

    bloom_available = _detect_bloom_filter()
    if not bloom_available:
        print("[WARNING] Bloom filter not detected; benchmarking unoptimized build.")
    else:
        print("[INFO] Bloom filter optimization detected.")

    total_runs = args.total_runs
    discard = args.discard
    keep_from = discard
    keep_to = total_runs - discard

    index_dir = tempfile.mkdtemp(prefix="whoosh_bloom_experiment_")
    try:
        print(f"Building index with {args.docs} documents (bloom enabled)...")
        build_index(index_dir, args.docs)

        # Verify bloom file was created
        blm_files = [f for f in os.listdir(index_dir) if f.endswith(".blm")]
        if blm_files:
            print(f"[INFO] Bloom filter file(s) created: {blm_files}")
        else:
            print("[WARNING] No .blm file found — bloom filter may not have been written.")

        ix = index.open_dir(index_dir)
        absent_terms = generate_absent_queries(args.absent_queries, args.docs)

        print(f"Running {total_runs} iterations ({discard} warmup, {discard} cooldown, "
              f"{keep_to - keep_from} measured)...")
        all_timings = []
        for i in range(total_runs):
            elapsed = run_benchmark(ix, absent_terms)
            all_timings.append(elapsed)
            print(f"  run {i + 1}/{total_runs}: {elapsed:.2f} ms")

        ix.close()
    finally:
        shutil.rmtree(index_dir, ignore_errors=True)

    measured = all_timings[keep_from:keep_to]
    mean_ms = statistics.mean(measured)
    std_ms = statistics.stdev(measured)
    median_ms = statistics.median(measured)

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
        "experiment": "bloom-filter-negative-lookup",
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
            "median_ms": round(median_ms, 4),
            "runs": len(measured),
            "total_runs": total_runs,
            "discarded_warmup": discard,
            "discarded_cooldown": discard,
        },
        "improvement_pct": round(improvement_pct, 2) if improvement_pct is not None else None,
        "improvement_confirmed": improvement_confirmed,
        "config": {
            "docs": args.docs,
            "absent_queries_per_run": args.absent_queries,
            "seed": args.seed,
        },
    }

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    print(f"\nResults: mean={mean_ms:.2f} ms, std={std_ms:.2f} ms, median={median_ms:.2f} ms")
    if improvement_pct is not None:
        print(f"Improvement: {improvement_pct:.2f}% (confirmed={improvement_confirmed})")
    print(f"Experiment saved to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
