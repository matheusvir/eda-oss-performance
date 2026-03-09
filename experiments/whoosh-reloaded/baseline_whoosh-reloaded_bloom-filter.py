"""Baseline benchmark for negative term lookups without Bloom filter.

Indexes 500k documents and queries for 1000 absent terms per run.
This script runs against vanilla whoosh (no bloom filter optimization),
so every negative lookup goes through the full on-disk hash table.

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
        description="Baseline: negative term lookup performance without Bloom filter"
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
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


_DOC_PREFIX = "existingterm"
_ABSENT_PREFIX = "absentterm"


def _existing_token(i: int) -> str:
    """Generate a token that will exist in the index."""
    return f"{_DOC_PREFIX}{i:08d}"


def _absent_token(i: int) -> str:
    """Generate a token guaranteed to NOT exist in the index."""
    return f"{_ABSENT_PREFIX}{i:08d}"


def build_index(index_dir: str, doc_count: int) -> None:
    """Build a whoosh index using the default codec (no bloom filter).

    This runs against vanilla whoosh where bloom filter support does not
    exist, so no special codec configuration is needed.

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

    total_runs = args.total_runs
    discard = args.discard
    keep_from = discard
    keep_to = total_runs - discard

    index_dir = tempfile.mkdtemp(prefix="whoosh_bloom_baseline_")
    try:
        print(f"Building index with {args.docs} documents (vanilla whoosh, no bloom)...")
        build_index(index_dir, args.docs)
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

    result = {
        "experiment": "bloom-filter-negative-lookup",
        "project": "whoosh-reloaded",
        "variant": "baseline",
        "baseline": {
            "mean_ms": round(mean_ms, 4),
            "std_ms": round(std_ms, 4),
            "median_ms": round(median_ms, 4),
            "runs": len(measured),
            "total_runs": total_runs,
            "discarded_warmup": discard,
            "discarded_cooldown": discard,
        },
        "optimized": {"mean_ms": None, "std_ms": None, "median_ms": None, "runs": None},
        "improvement_pct": None,
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
    print(f"Baseline saved to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
