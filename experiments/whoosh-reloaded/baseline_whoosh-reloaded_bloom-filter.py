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
        description="Baseline: negative-lookup performance without Bloom Filter"
    )
    parser.add_argument("--docs", type=int, default=500_000)
    parser.add_argument("--queries", type=int, default=1_000)
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument(
        "--output",
        type=str,
        default="/results/result_whoosh-reloaded_bloom-filter.json",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


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

    index_dir = tempfile.mkdtemp(prefix="whoosh_bloom_baseline_")
    try:
        indexed_words = build_index(index_dir, args.docs, rng)
        absent_terms = generate_absent_terms(indexed_words, args.queries, rng)
        ix = index.open_dir(index_dir)

        run_benchmark(ix, absent_terms)  # warm-up

        timings_ms = [run_benchmark(ix, absent_terms) for _ in range(args.runs)]
        ix.close()
    finally:
        shutil.rmtree(index_dir, ignore_errors=True)

    mean_ms = statistics.mean(timings_ms)
    std_ms = statistics.stdev(timings_ms)

    result = {
        "experiment": "bloom-filter-negative-lookup",
        "project": "whoosh-reloaded",
        "variant": "baseline",
        "baseline": {
            "mean_ms": round(mean_ms, 4),
            "std_ms": round(std_ms, 4),
            "runs": args.runs,
        },
        "optimized": {"mean_ms": None, "std_ms": None, "runs": None},
        "improvement_pct": None,
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

    print(f"baseline saved to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
