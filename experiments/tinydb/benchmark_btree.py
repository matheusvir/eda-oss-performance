"""
Benchmark: B-Tree Index optimization in TinyDB

Measures the impact of the B-Tree index on equality queries
(Query().field == value). Without an index, TinyDB performs a full scan
over every document in the table. With a B-Tree index created via
``table.create_index(field)``, the lookup runs in O(log n).

Methodology:
  - 50 runs per scenario
  - Discard first 10 (warmup) and last 10 (cooldown)
  - Use middle 30 runs for statistics
  - Test with JSONStorage (real file I/O)
  - Multiple document counts: 1_000, 10_000, 50_000
  - Each run performs LOOKUPS_PER_RUN equality searches
    (half for existing values, half for nonexistent values)
"""

import gc
import json
import os
import statistics
import sys
import tempfile
import time

sys.path.insert(0, '/app/tinydb')

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage

TOTAL_RUNS = 50
DISCARD = 10  # discard first 10 and last 10
DOC_SIZES = [1_000, 10_000, 50_000]
LOOKUPS_PER_RUN = 100  # equality searches per run


def create_db(path, num_docs):
    """Create a TinyDB with num_docs documents and return the db instance."""
    db = TinyDB(path, storage=JSONStorage)
    docs = [{"category": f"cat_{i % 200}", "value": i, "data": "x" * 50}
            for i in range(num_docs)]
    db.insert_multiple(docs)
    return db


def run_searches(db, num_docs):
    """
    Perform LOOKUPS_PER_RUN equality searches.
    Half target existing values, half target nonexistent values.
    """
    Item = Query()
    half = LOOKUPS_PER_RUN // 2

    # Existing values — spread across the document range
    step = max(1, num_docs // half)
    for i in range(half):
        db.search(Item.value == (i * step))

    # Nonexistent values — guaranteed absent
    base = num_docs + 1000
    for i in range(half):
        db.search(Item.value == (base + i))


def benchmark_scenario(num_docs, use_index):
    """Run the benchmark for a given doc count and index setting."""
    all_times = []

    for _ in range(TOTAL_RUNS):
        tmp = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        tmp_path = tmp.name
        tmp.close()

        try:
            db = create_db(tmp_path, num_docs)

            if use_index:
                table = db.table('_default')
                table.create_index('value')

            # Warm the storage cache with one read
            db.search(Query().value == 0)
            # Clear the query cache so we measure actual lookups
            db.clear_cache()

            gc.collect()
            gc.disable()

            start = time.perf_counter()
            run_searches(db, num_docs)
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

    print(f"{'Docs':>10} | {'Variant':<12} | {'Mean (ms)':>12} | "
          f"{'Std (ms)':>12} | Runs used")
    print("-" * 70)

    for num_docs in DOC_SIZES:
        print(f"\n--- Benchmarking with {num_docs:,} documents ---")

        # Baseline: no index (full scan)
        baseline_times = benchmark_scenario(num_docs, use_index=False)
        b_mean = statistics.mean(baseline_times)
        b_std = statistics.stdev(baseline_times)

        print(f"{num_docs:>10,} | {'baseline':<12} | {b_mean:>12.4f} | "
              f"{b_std:>12.4f} | {len(baseline_times)}")

        # Optimized: B-Tree index
        optimized_times = benchmark_scenario(num_docs, use_index=True)
        o_mean = statistics.mean(optimized_times)
        o_std = statistics.stdev(optimized_times)

        print(f"{num_docs:>10,} | {'btree':<12} | {o_mean:>12.4f} | "
              f"{o_std:>12.4f} | {len(optimized_times)}")

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
            print(f"  -> COMPROVADA: reducao {diff_abs:.4f}ms > "
                  f"desvio padrao {b_std:.4f}ms")
        else:
            print(f"  -> NAO comprovada: reducao {diff_abs:.4f}ms <= "
                  f"desvio padrao {b_std:.4f}ms")

    # Build output in the required format
    output = {
        "experiment": "btree-document-index",
        "project": "tinydb",
        "methodology": {
            "total_runs": TOTAL_RUNS,
            "discarded_warmup": DISCARD,
            "discarded_cooldown": DISCARD,
            "effective_runs": TOTAL_RUNS - 2 * DISCARD,
            "lookups_per_run": LOOKUPS_PER_RUN,
            "storage": "JSONStorage",
            "operation": "search(Query().field == value)",
        },
        "scales": results_all,
    }

    os.makedirs("results/tinydb", exist_ok=True)
    out_path = "results/tinydb/result_tinydb_btree.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {out_path}")
    print(json.dumps(output, indent=2))

    # Print comparative table
    print("\n" + "=" * 90)
    print("TABELA COMPARATIVA - B-Tree Index vs Baseline (equality queries)")
    print("=" * 90)
    print(f"{'Documentos':>12} | {'Baseline (ms)':>14} | {'B-Tree (ms)':>14} "
          f"| {'Diff (ms)':>12} | {'Melhoria (%)':>13}")
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
