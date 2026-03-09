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
from whoosh.fields import ID, NGRAM, NGRAMWORDS, Schema


def parse_args():
    parser = argparse.ArgumentParser(
        description="Baseline: N-gram tokenization and indexing performance"
    )
    parser.add_argument("--docs", type=int, default=10_000)
    parser.add_argument("--doc-length", type=int, default=500)
    parser.add_argument("--queries", type=int, default=200)
    parser.add_argument("--min-ngram", type=int, default=2)
    parser.add_argument("--max-ngram", type=int, default=4)
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument(
        "--output",
        type=str,
        default="/results/result_whoosh-reloaded_ngrams.json",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


_WORDS = [
    "performance", "algorithm", "structure", "database", "indexing",
    "searching", "optimize", "analysis", "document", "filtering",
    "benchmark", "ngram", "tokenizer", "encoding", "characters",
    "frequency", "matching", "position", "storage", "efficient",
    "parallel", "computing", "function", "iterator", "generator",
]


def generate_text(rng, length):
    words = []
    current_len = 0
    while current_len < length:
        word = rng.choice(_WORDS)
        words.append(word)
        current_len += len(word) + 1
    return " ".join(words)[:length]


def generate_query(rng, min_ngram, max_ngram):
    word = rng.choice(_WORDS)
    size = rng.randint(min_ngram, min(max_ngram, len(word)))
    start = rng.randint(0, len(word) - size)
    return word[start:start + size]


def build_index(index_dir, args, rng):
    schema = Schema(
        id=ID(stored=True),
        ngram_content=NGRAM(
            minsize=args.min_ngram,
            maxsize=args.max_ngram,
            stored=False,
        ),
        ngramword_content=NGRAMWORDS(
            minsize=args.min_ngram,
            maxsize=args.max_ngram,
            stored=False,
        ),
    )
    ix = index.create_in(index_dir, schema)
    writer = ix.writer()

    for i in range(args.docs):
        text = generate_text(rng, args.doc_length)
        writer.add_document(
            id=str(i),
            ngram_content=text,
            ngramword_content=text,
        )

    writer.commit()
    return ix


def run_search_benchmark(ix, queries, field):
    from whoosh.query import Term

    searcher = ix.searcher()

    start = time.perf_counter()
    for q_text in queries:
        q = Term(field, q_text)
        _ = len(searcher.search(q, limit=10))
    end = time.perf_counter()

    searcher.close()
    return (end - start) * 1_000.0


def run_indexing_benchmark(args, rng):
    index_dir = tempfile.mkdtemp(prefix="whoosh_ngram_idx_bench_")
    try:
        start = time.perf_counter()
        ix = build_index(index_dir, args, rng)
        end = time.perf_counter()
        ix.close()
    finally:
        shutil.rmtree(index_dir, ignore_errors=True)
    return (end - start) * 1_000.0


def main():
    args = parse_args()
    rng = random.Random(args.seed)

    texts = [generate_text(rng, args.doc_length) for _ in range(args.docs)]
    queries = [generate_query(rng, args.min_ngram, args.max_ngram) for _ in range(args.queries)]

    # --- Benchmark 1: Indexing ---
    # Warm-up
    run_indexing_benchmark(args, random.Random(args.seed))

    indexing_timings = []
    for _ in range(args.runs):
        ms = run_indexing_benchmark(args, random.Random(args.seed))
        indexing_timings.append(ms)

    # --- Benchmark 2: Searching ---
    index_dir = tempfile.mkdtemp(prefix="whoosh_ngram_search_bench_")
    try:
        ix = build_index(index_dir, args, random.Random(args.seed))

        # Warm-up
        run_search_benchmark(ix, queries, "ngram_content")

        search_timings = []
        for _ in range(args.runs):
            ms = run_search_benchmark(ix, queries, "ngram_content")
            search_timings.append(ms)

        ix.close()
    finally:
        shutil.rmtree(index_dir, ignore_errors=True)

    # --- Benchmark 3: NgramTokenizer throughput ---
    from whoosh.analysis import NgramTokenizer

    tokenizer = NgramTokenizer(args.min_ngram, args.max_ngram)
    big_text = generate_text(rng, 5000)

    # Warm-up
    list(tokenizer(big_text))

    tokenizer_timings = []
    for _ in range(args.runs):
        start = time.perf_counter()
        for text in texts[:500]:
            _ = list(tokenizer(text))
        end = time.perf_counter()
        tokenizer_timings.append((end - start) * 1_000.0)

    # --- Aggregate results ---
    total_timings = [
        idx + srch + tok
        for idx, srch, tok in zip(indexing_timings, search_timings, tokenizer_timings)
    ]

    mean_ms = statistics.mean(total_timings)
    std_ms = statistics.stdev(total_timings)

    result = {
        "experiment": "ngrams",
        "project": "whoosh-reloaded",
        "variant": "baseline",
        "baseline": {
            "mean_ms": round(mean_ms, 4),
            "std_ms": round(std_ms, 4),
            "runs": args.runs,
        },
        "optimized": {"mean_ms": None, "std_ms": None, "runs": None},
        "improvement_pct": None,
        "details": {
            "indexing": {
                "mean_ms": round(statistics.mean(indexing_timings), 4),
                "std_ms": round(statistics.stdev(indexing_timings), 4),
            },
            "searching": {
                "mean_ms": round(statistics.mean(search_timings), 4),
                "std_ms": round(statistics.stdev(search_timings), 4),
            },
            "tokenizer": {
                "mean_ms": round(statistics.mean(tokenizer_timings), 4),
                "std_ms": round(statistics.stdev(tokenizer_timings), 4),
            },
        },
        "config": {
            "docs": args.docs,
            "doc_length": args.doc_length,
            "queries": args.queries,
            "min_ngram": args.min_ngram,
            "max_ngram": args.max_ngram,
            "seed": args.seed,
        },
    }

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    print(f"baseline saved to: {args.output}")
    print(f"  total:     mean={mean_ms:.2f} ms, std={std_ms:.2f} ms")
    print(f"  indexing:  mean={statistics.mean(indexing_timings):.2f} ms")
    print(f"  searching: mean={statistics.mean(search_timings):.2f} ms")
    print(f"  tokenizer: mean={statistics.mean(tokenizer_timings):.2f} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
