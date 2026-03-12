"""
generate_plots.py

Generates all benchmark comparison charts for the EDA OSS Performance project.
All labels and titles are in English.

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
    ax.errorbar(x - width / 2, baseline_means,  yerr=baseline_stds,  color="#b91c1c", **ERROR_KWARGS)
    ax.errorbar(x + width / 2, optimized_means, yerr=optimized_stds, color="#15803d", **ERROR_KWARGS)

    # Improvement annotations above optimized bars
    for bar, pct in zip(bars_o, improvements):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(baseline_stds) * 0.02,
                f"−{pct:.1f}%", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#15803d")

    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f} ms"))
    ax.set_xticks(x)
    ax.set_xticklabels([f"{lbl} docs" for lbl in labels])
    ax.set_xlabel("Dataset size")
    ax.set_ylabel("Mean time per 100 negative lookups (ms, log scale)")
    ax.set_title("TinyDB — Bloom Filter: Negative Lookup Performance\n(100 absent doc_id lookups per run, JSONStorage)")
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
    ax.errorbar(x - width / 2, baseline_means,  yerr=baseline_stds,  color="#b91c1c", **ERROR_KWARGS)
    ax.errorbar(x + width / 2, optimized_means, yerr=optimized_stds, color="#15803d", **ERROR_KWARGS)

    for bar, pct in zip(bars_o, improvements):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(baseline_stds) * 0.02,
                f"−{pct:.1f}%", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#15803d")

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f} ms"))
    ax.set_xticks(x)
    ax.set_xticklabels([f"{lbl} docs" for lbl in labels])
    ax.set_xlabel("Dataset size")
    ax.set_ylabel("Mean time per 100 equality queries (ms)")
    ax.set_title("TinyDB — B-Tree Index: Equality Search Performance\n(100 search(Query().field == value) per run, JSONStorage)")
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
        "python-dotenv — ChainMap: Load Performance (interpolation disabled)\n"
        "dotenv_values() — 50 runs per scale, 30 scale points",
        "dotenv_chainmap_no_interpolation.png",
    )


# -------------------------------------------------------------------------
# 4. python-dotenv — ChainMap (with interpolation)
# -------------------------------------------------------------------------
def plot_chainmap_interp() -> None:
    _plot_chainmap(
        os.path.join(RESULTS_DIR, "python-dotenv", "result_interpolation_dotenv_chainmap.json"),
        "python-dotenv — ChainMap: Load Performance (interpolation enabled)\n"
        "dotenv_values() — 50 runs per scale, 30 scale points",
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
    ax.errorbar([0, 1], [b_mean, o_mean], yerr=[b_std, o_std],
                color="black", **ERROR_KWARGS)
    ax.text(1, o_mean + o_std + 100, f"−{improvement:.1f}%",
            ha="center", va="bottom", fontsize=10, fontweight="bold", color="#15803d")

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f} ms"))
    ax.set_ylabel("Mean full-file parse time (ms)")
    ax.set_title("python-dotenv — str.count: Parser Performance\n"
                 f"(24,999 variables | baseline n={data['baseline']['runs']}, "
                 f"optimized n={data['optimized']['runs']})")
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
    ax.errorbar([0, 1], [b_mean, o_mean], yerr=[b_std, o_std],
                color="black", **ERROR_KWARGS)

    label = f"−{improvement:.2f}%"
    label += " ✓" if confirmed else " *"
    ax.text(1, o_mean + o_std * 0.3 + (b_mean - o_mean) * 0.05,
            label, ha="center", va="bottom", fontsize=10, fontweight="bold",
            color="#15803d" if confirmed else "#ca8a04")

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.2f} ms"))
    ax.set_ylabel(ylabel)
    note = "(* difference < baseline std dev — improvement objective but not confirmed by strict criterion)" if not confirmed else ""
    ax.set_title(f"{title}\n(baseline n={b_runs}, optimized n={o_runs}){chr(10)+note if note else ''}", fontsize=9.5)
    fig.tight_layout()
    save(fig, out_subdir, out_name)


# -------------------------------------------------------------------------
# 6. whoosh-reloaded — Skip Lists
# -------------------------------------------------------------------------
def plot_whoosh_skip_lists() -> None:
    _plot_whoosh_simple(
        os.path.join(RESULTS_DIR, "whoosh-reloaded", "result_whoosh-reloaded_skip-lists.json"),
        "whoosh-reloaded — Skip Lists: AND Intersection Performance\n"
        "(500k docs, 100 AND query pairs per run)",
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
        "whoosh-reloaded — Bloom Filter: Negative Term Lookup Performance\n"
        "(500k docs, 1,000 absent-term queries per run)",
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
        "whoosh-reloaded — N-gram Index: Prefix-less Wildcard Performance\n"
        "(30k docs, 40 wildcard queries per run: *ados, *ritmo*, *logia, *graf*)",
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
