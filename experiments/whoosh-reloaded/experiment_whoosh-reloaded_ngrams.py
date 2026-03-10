"""Experiment benchmark for wildcard lookup with ngram acceleration.

This benchmark measures wildcard queries that do not have a literal prefix
(e.g. ``*ados`` and ``*ritmo*``). In optimized behavior, these queries use
an ngram candidate index instead of a full linear scan over lexicon terms.

Methodology:
  - 50 runs total
  - Discard first 10 (warmup) and last 10 (cooldown)
  - Use middle 30 runs for statistics
  - GC disabled during measurement
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
from itertools import product
from typing import Dict, List

import whoosh.index as index
from whoosh.fields import ID, TEXT, Schema
from whoosh.query import Wildcard

TOTAL_RUNS = 50
DISCARD = 10
DEFAULT_PATTERNS = "*ados,*ritmo*,*logia,*graf*"

PREFIXES = (
    "bio", "neuro", "hidro", "termo", "eletro", "micro", "macro", "crono",
    "geo", "aero", "foto", "quimio", "orto", "cardio", "hemo", "cito",
    "nano", "tele", "socio", "psico", "radio", "econo", "mecano", "astro",
)
MIDDLES = (
    "ritmo", "dado", "modelo", "sinal", "sistema", "process", "algoritmo",
    "metodo", "estrutura", "teoria", "analise", "dinamica", "sintese",
    "controle", "mecanismo", "graf", "vetor", "filtro", "indice", "codigo",
)
SUFFIXES = (
    "ados", "ico", "ica", "ismo", "ista", "logia", "metria", "grafia",
    "vel", "tivo", "izacao", "ante", "ente", "ar", "ario", "al",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Experiment: wildcard lookup performance with ngram candidate index"
        )
    )
    parser.add_argument("--vocab-size", type=int, default=7_000)
    parser.add_argument("--docs", type=int, default=200_000)
    parser.add_argument("--wildcards-per-run", type=int, default=400)
    parser.add_argument("--patterns", type=str, default=DEFAULT_PATTERNS)
    parser.add_argument("--total-runs", type=int, default=TOTAL_RUNS)
    parser.add_argument("--discard", type=int, default=DISCARD)
    parser.add_argument(
        "--output",
        type=str,
        default="/results/result_whoosh-reloaded_ngrams.json",
    )
    parser.add_argument("--baseline", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def build_vocabulary(vocab_size: int) -> List[str]:
    terms: List[str] = []
    for pref, mid, suff in product(PREFIXES, MIDDLES, SUFFIXES):
        terms.append(f"{pref}{mid}{suff}")
        if len(terms) == vocab_size:
            return terms

    raise ValueError(
        "vocab_size too large for generated cartesian vocabulary; "
        f"max supported is {len(PREFIXES) * len(MIDDLES) * len(SUFFIXES)}"
    )


def parse_patterns(patterns: str) -> List[str]:
    parsed = [p.strip() for p in patterns.split(",") if p.strip()]
    if not parsed:
        raise ValueError("patterns cannot be empty")
    return parsed


def build_index(index_dir: str, docs: int, vocab: List[str]) -> None:
    schema = Schema(id=ID(stored=True), content=TEXT(stored=False))
    ix = index.create_in(index_dir, schema)
    writer = ix.writer()

    vocab_len = len(vocab)
    for i in range(docs):
        writer.add_document(id=str(i), content=vocab[i % vocab_len])

    writer.commit()


def build_run_patterns(patterns: List[str], wildcards_per_run: int) -> List[str]:
    run_patterns: List[str] = []
    while len(run_patterns) < wildcards_per_run:
        run_patterns.extend(patterns)
    return run_patterns[:wildcards_per_run]


def count_matches(ix: index.Index, patterns: List[str]) -> Dict[str, int]:
    searcher = ix.searcher()
    counts: Dict[str, int] = {}
    for pattern in patterns:
        query = Wildcard("content", pattern)
        counts[pattern] = len(searcher.search(query, limit=None))
    searcher.close()
    return counts


def run_benchmark(ix: index.Index, run_patterns: List[str]) -> float:
    searcher = ix.searcher()
    queries = [Wildcard("content", p) for p in run_patterns]

    gc.collect()
    gc.disable()
    start = time.perf_counter()
    for query in queries:
        _ = searcher.search(query, limit=10)
    end = time.perf_counter()
    gc.enable()

    searcher.close()
    return (end - start) * 1_000.0


def main() -> int:
    args = parse_args()

    if args.discard * 2 >= args.total_runs:
        raise ValueError("discard must be less than total_runs / 2")

    patterns = parse_patterns(args.patterns)
    vocab = build_vocabulary(args.vocab_size)
    run_patterns = build_run_patterns(patterns, args.wildcards_per_run)

    keep_from = args.discard
    keep_to = args.total_runs - args.discard

    index_dir = tempfile.mkdtemp(prefix="whoosh_ngrams_experiment_")
    try:
        print(f"Building index with docs={args.docs}, vocab={args.vocab_size}...")
        build_index(index_dir, args.docs, vocab)
        ix = index.open_dir(index_dir)

        matches = count_matches(ix, patterns)
        print(f"Wildcard patterns: {patterns}")
        print(f"Matches per pattern: {matches}")
        print(
            f"Running {args.total_runs} iterations "
            f"({args.discard} warmup, {args.discard} cooldown, {keep_to - keep_from} measured)..."
        )

        all_timings: List[float] = []
        for i in range(args.total_runs):
            elapsed = run_benchmark(ix, run_patterns)
            all_timings.append(elapsed)
            print(f"  run {i + 1}/{args.total_runs}: {elapsed:.2f} ms")

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
            baseline_data = json.load(fh)
        baseline_mean = baseline_data.get("baseline", {}).get("mean_ms")
        baseline_std = baseline_data.get("baseline", {}).get("std_ms")
        baseline_runs = baseline_data.get("baseline", {}).get("runs")

        if baseline_mean and baseline_mean > 0:
            improvement_pct = ((baseline_mean - mean_ms) / baseline_mean) * 100.0
            if baseline_std is not None:
                improvement_confirmed = mean_ms < (baseline_mean - baseline_std)

    result = {
        "experiment": "ngrams-wildcard",
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
            "total_runs": args.total_runs,
            "discarded_warmup": args.discard,
            "discarded_cooldown": args.discard,
        },
        "improvement_pct": round(improvement_pct, 2) if improvement_pct is not None else None,
        "improvement_confirmed": improvement_confirmed,
        "config": {
            "docs": args.docs,
            "vocab_size": args.vocab_size,
            "wildcards_per_run": args.wildcards_per_run,
            "patterns": patterns,
            "pattern_match_counts": matches,
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
