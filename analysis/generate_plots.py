"""
generate_plots.py

Generates all benchmark comparison charts for the EDA OSS Performance project.

Usage:
    python analysis/generate_plots.py

Output:
    analysis/plots/<project>/<chart>.png
"""

import json
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# --- Style config ---
COLORS = {
    "baseline": "#ef4444",   # red
    "optimized": "#22c55e",  # green
}
ERROR_KWARGS = dict(fmt="none", elinewidth=1.5, capsize=5, zorder=3)
ALPHA_BAR = 0.88
FONT_FAMILY = "DejaVu Sans"

plt.rcParams.update({
    "font.family": FONT_FAMILY,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
})

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "results")
PLOTS_DIR = os.path.join(ROOT, "analysis", "plots")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save(fig: plt.Figure, subdir: str, name: str) -> None:
    out = os.path.join(PLOTS_DIR, subdir)
    ensure_dir(out)
    path = os.path.join(out, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {os.path.relpath(path, ROOT)}")


# -------------------------------------------------------------------------
# 1. TinyDB — Bloom Filter (multi-scale grouped bar chart)
# -------------------------------------------------------------------------
def plot_tinydb_bloom_filter() -> None:
    with open(os.path.join(RESULTS_DIR, "tinydb", "result_tinydb_bloom-filter.json")) as f:
        data = json.load(f)

    scales = data["scales"]
    labels = [f"{s['num_docs']:,}" for s in scales]
    baseline_means = [s["baseline_mean_ms"] for s in scales]
    baseline_stds  = [s["baseline_std_ms"]  for s in scales]
    optimized_means = [s["optimized_mean_ms"] for s in scales]
    optimized_stds  = [s["optimized_std_ms"]  for s in scales]
    improvements    = [s["improvement_pct"]   for s in scales]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    bars_b = ax.bar(x - width / 2, baseline_means,  width, label="Baseline",  color=COLORS["baseline"],  alpha=ALPHA_BAR)
    bars_o = ax.bar(x + width / 2, optimized_means, width, label="Optimized", color=COLORS["optimized"], alpha=ALPHA_BAR)
    # Add time values on top of baseline bars
    for bar, val in zip(bars_b, baseline_means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{val:,.0f} ms", ha="center", va="bottom", fontsize=8)

    # Add time values on top of optimized bars
    for bar, val, pct in zip(bars_o, optimized_means, improvements):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{val:,.0f} ms\n(▼ {pct:.1f}%)", ha="center", va="bottom", fontsize=8, color="#15803d")

    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f} ms"))
    ax.set_xticks(x)
    ax.set_xticklabels([f"{lbl} docs" for lbl in labels])
    ax.set_xlabel("Dataset size")
    ax.set_ylabel("Mean time per 100 negative lookups (ms, log scale)")
    ax.set_title("TinyDB: Bloom Filter")
    ax.legend()
    fig.tight_layout()
    save(fig, "tinydb", "tinydb_bloom_filter_comparison.png")


# -------------------------------------------------------------------------
# 2. TinyDB — B-Tree (multi-scale grouped bar chart)
# -------------------------------------------------------------------------
def plot_tinydb_btree() -> None:
    with open(os.path.join(RESULTS_DIR, "tinydb", "result_tinydb_btree.json")) as f:
        data = json.load(f)

    scales = data["scales"]
    labels = [f"{s['num_docs']:,}" for s in scales]
    baseline_means = [s["baseline_mean_ms"] for s in scales]
    baseline_stds  = [s["baseline_std_ms"]  for s in scales]
    optimized_means = [s["optimized_mean_ms"] for s in scales]
    optimized_stds  = [s["optimized_std_ms"]  for s in scales]
    improvements    = [s["improvement_pct"]   for s in scales]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    bars_b = ax.bar(x - width / 2, baseline_means,  width, label="Baseline",  color=COLORS["baseline"],  alpha=ALPHA_BAR)
    bars_o = ax.bar(x + width / 2, optimized_means, width, label="Optimized", color=COLORS["optimized"], alpha=ALPHA_BAR)
    for bar, val in zip(bars_b, baseline_means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{val:,.0f} ms", ha="center", va="bottom", fontsize=8)

    for bar, val, pct in zip(bars_o, optimized_means, improvements):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{val:,.0f} ms\n(▼ {pct:.1f}%)", ha="center", va="bottom", fontsize=8, color="#15803d")

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f} ms"))
    ax.set_xticks(x)
    ax.set_xticklabels([f"{lbl} docs" for lbl in labels])
    ax.set_xlabel("Dataset size")
    ax.set_ylabel("Mean time per 100 equality queries (ms)")
    ax.set_title("TinyDB: B-Tree Index")
    ax.legend()
    fig.tight_layout()
    save(fig, "tinydb", "tinydb_btree_comparison.png")


# -------------------------------------------------------------------------
# Helper: ChainMap line chart (no-interp / interp)
# -------------------------------------------------------------------------
def _plot_chainmap(json_path: str, title: str, out_name: str) -> None:
    with open(json_path) as f:
        records = json.load(f)

    # filter records where both means are available
    xs      = [r["num_variables"] for r in records]
    b_means = [r["baseline"]["mean_ms"]  for r in records]
    b_stds  = [r["baseline"]["std_ms"]   for r in records]
    o_means = [r["optimized"]["mean_ms"] for r in records]
    o_stds  = [r["optimized"]["std_ms"]  for r in records]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(xs, b_means, label="Baseline",  color=COLORS["baseline"],  linewidth=2)
    ax.fill_between(xs,
                    [m - s for m, s in zip(b_means, b_stds)],
                    [m + s for m, s in zip(b_means, b_stds)],
                    color=COLORS["baseline"], alpha=0.15)
    ax.plot(xs, o_means, label="Optimized", color=COLORS["optimized"], linewidth=2)
    ax.fill_between(xs,
                    [m - s for m, s in zip(o_means, o_stds)],
                    [m + s for m, s in zip(o_means, o_stds)],
                    color=COLORS["optimized"], alpha=0.15)

    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f} ms"))
    ax.set_xlabel("Number of .env variables (log scale)")
    ax.set_ylabel("Mean load time (ms)")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    save(fig, "python-dotenv", out_name)


# -------------------------------------------------------------------------
# 3. python-dotenv — ChainMap (no interpolation)
# -------------------------------------------------------------------------
def plot_chainmap_no_interp() -> None:
    _plot_chainmap(
        os.path.join(RESULTS_DIR, "python-dotenv", "result_no_interpolation_dotenv_chainmap.json"),
        "Python-dotenv: ChainMap (no interpolation)",
        "dotenv_chainmap_no_interpolation.png",
    )


# -------------------------------------------------------------------------
# 4. python-dotenv — ChainMap (with interpolation)
# -------------------------------------------------------------------------
def plot_chainmap_interp() -> None:
    _plot_chainmap(
        os.path.join(RESULTS_DIR, "python-dotenv", "result_interpolation_dotenv_chainmap.json"),
        "Python-dotenv: ChainMap (with interpolation)",
        "dotenv_chainmap_interpolation.png",
    )


# -------------------------------------------------------------------------
# 5. python-dotenv — str.count (simple bar)
# -------------------------------------------------------------------------
def plot_str_count() -> None:
    with open(os.path.join(RESULTS_DIR, "python-dotenv", "result_python-dotenv_str-count-newline-advance.json")) as f:
        data = json.load(f)

    b_mean, b_std = data["baseline"]["mean_ms"],  data["baseline"]["std_ms"]
    o_mean, o_std = data["optimized"]["mean_ms"], data["optimized"]["std_ms"]
    improvement   = data["improvement_pct"]

    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar(["Baseline", "Optimized"], [b_mean, o_mean],
                  color=[COLORS["baseline"], COLORS["optimized"]], alpha=ALPHA_BAR, width=0.4)
    ax.text(0, b_mean, f"{b_mean:,.0f} ms", ha="center", va="bottom", fontsize=10)
    ax.text(1, o_mean, f"{o_mean:,.0f} ms\n(▼ {improvement:.1f}%)", ha="center", va="bottom", fontsize=10, color="#15803d")

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f} ms"))
    ax.set_ylabel("Mean full-file parse time (ms)")
    ax.set_title("Python-dotenv: str.count Parser")
    fig.tight_layout()
    save(fig, "python-dotenv", "dotenv_str_count_newline.png")


# -------------------------------------------------------------------------
# Helper: simple 2-bar chart for whoosh experiments
# -------------------------------------------------------------------------
def _plot_whoosh_simple(json_path: str, title: str, ylabel: str, out_subdir: str, out_name: str) -> None:
    with open(json_path) as f:
        data = json.load(f)

    b_mean, b_std = data["baseline"]["mean_ms"],  data["baseline"]["std_ms"]
    o_mean, o_std = data["optimized"]["mean_ms"], data["optimized"]["std_ms"]
    improvement   = data["improvement_pct"]
    confirmed     = data.get("improvement_confirmed", False)
    b_runs        = data["baseline"]["runs"]
    o_runs        = data["optimized"]["runs"]

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.bar(["Baseline", "Optimized"], [b_mean, o_mean],
           color=[COLORS["baseline"], COLORS["optimized"]], alpha=ALPHA_BAR, width=0.4)
    ax.text(0, b_mean, f"{b_mean:,.2f} ms", ha="center", va="bottom", fontsize=10)
    label = f"{o_mean:,.2f} ms\n(▼ {improvement:.1f}%"
    label += " ✓)" if confirmed else " *)"
    ax.text(1, o_mean, label, ha="center", va="bottom", fontsize=10, color="#15803d" if confirmed else "#ca8a04")

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.2f} ms"))
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    save(fig, out_subdir, out_name)


# -------------------------------------------------------------------------
# 6. whoosh-reloaded — Skip Lists
# -------------------------------------------------------------------------
def plot_whoosh_skip_lists() -> None:
    _plot_whoosh_simple(
        os.path.join(RESULTS_DIR, "whoosh-reloaded", "result_whoosh-reloaded_skip-lists.json"),
        "Whoosh-Reloaded: Skip Lists",
        "Mean time per run (ms)",
        "whoosh-reloaded",
        "whoosh_skip_lists_comparison.png",
    )


# -------------------------------------------------------------------------
# 7. whoosh-reloaded — Bloom Filter
# -------------------------------------------------------------------------
def plot_whoosh_bloom_filter() -> None:
    _plot_whoosh_simple(
        os.path.join(RESULTS_DIR, "whoosh-reloaded", "result_whoosh-reloaded_bloom-filter.json"),
        "Whoosh-Reloaded: Bloom Filter",
        "Mean time per 1,000 absent queries (ms)",
        "whoosh-reloaded",
        "whoosh_bloom_filter_comparison.png",
    )


# -------------------------------------------------------------------------
# 8. whoosh-reloaded — N-grams wildcard
# -------------------------------------------------------------------------
def plot_whoosh_ngrams() -> None:
    _plot_whoosh_simple(
        os.path.join(RESULTS_DIR, "whoosh-reloaded", "result_whoosh-reloaded_ngrams.json"),
        "Whoosh-Reloaded: N-Grams Index",
        "Mean time per run (ms)",
        "whoosh-reloaded",
        "whoosh_ngrams_comparison.png",
    )


# -------------------------------------------------------------------------
if __name__ == "__main__":
    print("Generating charts…")
    plot_tinydb_bloom_filter()
    plot_tinydb_btree()
    plot_chainmap_no_interp()
    plot_chainmap_interp()
    plot_str_count()
    plot_whoosh_skip_lists()
    plot_whoosh_bloom_filter()
    plot_whoosh_ngrams()
    print("Done.")
