"""
Benchmark: Bloom Filter optimization in TinyDB

Measures the impact of the Bloom Filter on doc_id lookups (get/contains)
for IDs that do NOT exist in the database. The Bloom Filter allows TinyDB
to skip _read_table() entirely when it can guarantee the ID is absent,
avoiding file I/O and JSON parsing overhead.

Methodology:
  - 50 runs per scenario
  - Discard first 10 (warmup) and last 10 (cooldown)
  - Use middle 30 runs for statistics
  - Test with JSONStorage (real file I/O) to measure actual savings
  - Multiple document counts: 1_000, 10_000, 50_000
  - Each run performs 100 lookups of nonexistent doc_ids
    (get + contains = 200 bloom filter checks per run)
"""

import gc
import json
import os
import statistics
import sys
import tempfile
import time

sys.path.insert(0, '/app/tinydb')

from tinydb import TinyDB
from tinydb.storages import JSONStorage

TOTAL_RUNS = 50
DISCARD = 10  # discard first 10 and last 10
DOC_SIZES = [1_000, 10_000, 50_000]
LOOKUPS_PER_RUN = 100  # nonexistent IDs to look up per run


def create_db(path, num_docs, use_bloom):
    """Create a TinyDB with num_docs documents and return the db instance."""
    db = TinyDB(path, storage=JSONStorage)
    # Force creation of the default table with the desired bloom setting
    # Size the bloom filter to match the actual number of documents
    table = db.table(
        '_default',
        bloom_filter=use_bloom,
        bloom_expected_items=max(num_docs, 1000),
    )
    db._tables['_default'] = table

    docs = [{"field": f"value_{i}", "data": "x" * 50} for i in range(num_docs)]
    table.insert_multiple(docs)
    return db


def run_lookups(db, num_docs):
    """
    Look up LOOKUPS_PER_RUN doc_ids that definitely don't exist.
    IDs in TinyDB start at 1, so IDs > num_docs are guaranteed absent.
    """
    start_id = num_docs + 1000
    for i in range(LOOKUPS_PER_RUN):
        doc_id = start_id + i
        db.get(doc_id=doc_id)
        db.contains(doc_id=doc_id)


def benchmark_scenario(num_docs, use_bloom):
    """Run the benchmark for a given doc count and bloom setting."""
    all_times = []

    for run_idx in range(TOTAL_RUNS):
        tmp = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        tmp_path = tmp.name
        tmp.close()

        try:
            db = create_db(tmp_path, num_docs, use_bloom)

            # Force bloom filter initialization by doing one read
            _ = db.get(doc_id=1)

            # Force garbage collection before measurement
            gc.collect()
            gc.disable()

            start = time.perf_counter()
            run_lookups(db, num_docs)
            end = time.perf_counter()

            gc.enable()

            elapsed_ms = (end - start) * 1000
            all_times.append(elapsed_ms)

            db.close()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # Discard first DISCARD and last DISCARD, keep the middle
    trimmed = all_times[DISCARD: TOTAL_RUNS - DISCARD]
    return trimmed


def main():
    results_all = []

    print(f"{'Docs':>10} | {'Variant':<12} | {'Mean (ms)':>12} | {'Std (ms)':>12} | Runs used")
    print("-" * 70)

    for num_docs in DOC_SIZES:
        print(f"\n--- Benchmarking with {num_docs:,} documents ---")

        # Baseline: bloom_filter=False
        baseline_times = benchmark_scenario(num_docs, use_bloom=False)
        b_mean = statistics.mean(baseline_times)
        b_std = statistics.stdev(baseline_times)

        print(f"{num_docs:>10,} | {'baseline':<12} | {b_mean:>12.4f} | {b_std:>12.4f} | {len(baseline_times)}")

        # Optimized: bloom_filter=True
        optimized_times = benchmark_scenario(num_docs, use_bloom=True)
        o_mean = statistics.mean(optimized_times)
        o_std = statistics.stdev(optimized_times)

        print(f"{num_docs:>10,} | {'bloom':<12} | {o_mean:>12.4f} | {o_std:>12.4f} | {len(optimized_times)}")

        diff_abs = b_mean - o_mean
        if b_mean > 0:
            improvement_pct = (diff_abs / b_mean) * 100
        else:
            improvement_pct = 0.0

        results_all.append({
            "num_docs": num_docs,
            "baseline_mean_ms": round(b_mean, 4),
            "baseline_std_ms": round(b_std, 4),
            "optimized_mean_ms": round(o_mean, 4),
            "optimized_std_ms": round(o_std, 4),
            "diff_abs_ms": round(diff_abs, 4),
            "improvement_pct": round(improvement_pct, 2),
        })

        # Statistical validation
        if diff_abs > b_std:
            print(f"  -> COMPROVADA: reducao {diff_abs:.4f}ms > desvio padrao {b_std:.4f}ms")
        else:
            print(f"  -> NAO comprovada: reducao {diff_abs:.4f}ms <= desvio padrao {b_std:.4f}ms")

    # Build output in the required format
    output = {
        "experiment": "bloom-filter",
        "project": "tinydb",
        "methodology": {
            "total_runs": TOTAL_RUNS,
            "discarded_warmup": DISCARD,
            "discarded_cooldown": DISCARD,
            "effective_runs": TOTAL_RUNS - 2 * DISCARD,
            "lookups_per_run": LOOKUPS_PER_RUN,
            "storage": "JSONStorage",
            "operation": "get(doc_id=nonexistent) + contains(doc_id=nonexistent)",
        },
        "scales": results_all,
    }

    os.makedirs("results/tinydb", exist_ok=True)
    out_path = "results/tinydb/result_tinydb_bloom-filter.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {out_path}")
    print(json.dumps(output, indent=2))

    # Print comparative table
    print("\n" + "=" * 90)
    print("TABELA COMPARATIVA - Bloom Filter vs Baseline (doc_id lookups inexistentes)")
    print("=" * 90)
    print(f"{'Documentos':>12} | {'Baseline (ms)':>14} | {'Bloom (ms)':>14} | {'Diff (ms)':>12} | {'Melhoria (%)':>13}")
    print("-" * 90)
    for r in results_all:
        print(
            f"{r['num_docs']:>12,} | "
            f"{r['baseline_mean_ms']:>14.4f} | "
            f"{r['optimized_mean_ms']:>14.4f} | "
            f"{r['diff_abs_ms']:>12.4f} | "
            f"{r['improvement_pct']:>12.2f}%"
        )
    print("=" * 90)


if __name__ == "__main__":
    main()
