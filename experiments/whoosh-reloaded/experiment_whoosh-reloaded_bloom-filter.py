import argparse
import json
import os
import random
import shutil
import statistics
import string
import sys
import tempfile
import time

import whoosh.index as index
from whoosh.fields import ID, TEXT, Schema
from whoosh.qparser import QueryParser


def parse_args():
    parser = argparse.ArgumentParser(
        description="Experiment: negative-lookup performance with Bloom Filter"
    )
    parser.add_argument("--docs", type=int, default=500_000)
    parser.add_argument("--queries", type=int, default=1_000)
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument(
        "--output",
        type=str,
        default="/results/result_whoosh-reloaded_bloom-filter.json",
    )
    parser.add_argument("--baseline", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _detect_bloom_filter(ix) -> bool:
    try:
        reader = ix.reader()
        has_bloom = hasattr(reader, "bloom_filter") or hasattr(reader, "_bloom")
        reader.close()
        return has_bloom
    except Exception:
        return False


def _random_word(rng: random.Random, length: int = 8) -> str:
    return "".join(rng.choice(string.ascii_lowercase) for _ in range(length))


def build_index(index_dir: str, doc_count: int, rng: random.Random) -> set:
    schema = Schema(id=ID(stored=True), content=TEXT(stored=False))
    ix = index.create_in(index_dir, schema)
    writer = ix.writer()
    indexed_words: set = set()

    for i in range(doc_count):
        words = [_random_word(rng) for _ in range(5)]
        indexed_words.update(words)
        writer.add_document(id=str(i), content=" ".join(words))

    writer.commit()
    return indexed_words


def generate_absent_terms(indexed_words: set, count: int, rng: random.Random) -> list:
    absent = []
    while len(absent) < count:
        candidate = _random_word(rng, length=12)
        if candidate not in indexed_words:
            absent.append(candidate)
    return absent


def run_benchmark(ix, absent_terms: list) -> float:
    searcher = ix.searcher()
    parser = QueryParser("content", ix.schema)

    start = time.perf_counter()
    for term in absent_terms:
        q = parser.parse(term)
        _ = len(searcher.search(q, limit=1))
    end = time.perf_counter()

    searcher.close()
    return (end - start) * 1_000.0


def main():
    args = parse_args()
    rng = random.Random(args.seed)

    index_dir = tempfile.mkdtemp(prefix="whoosh_bloom_experiment_")
    try:
        indexed_words = build_index(index_dir, args.docs, rng)
        absent_terms = generate_absent_terms(indexed_words, args.queries, rng)
        ix = index.open_dir(index_dir)

        if not _detect_bloom_filter(ix):
            print("[WARNING] Bloom Filter not detected; benchmarking unoptimized build.")

        run_benchmark(ix, absent_terms)  # warm-up

        timings_ms = [run_benchmark(ix, absent_terms) for _ in range(args.runs)]
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
            "runs": args.runs,
        },
        "improvement_pct": round(improvement_pct, 2) if improvement_pct is not None else None,
        "improvement_confirmed": improvement_confirmed,
        "config": {
            "docs": args.docs,
            "queries_per_run": args.queries,
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
