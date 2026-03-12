"""Generate comparative performance plots (baseline vs optimized) for all experiments.

Reads JSON result files from results/<project>/ and writes PNG plots to
analysis/plots/<project>/ using Seaborn.

Usage:
    python experiments/analysis/generate_perf_plots.py
"""

import json
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import seaborn as sns

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
PLOTS = os.path.join(ROOT, "analysis", "plots")

PALETTE = {"Baseline": "#4C72B0", "Experimento": "#DD8452"}

sns.set_theme(style="whitegrid", font_scale=1.1)


def savefig(fig: plt.Figure, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved: {path}")


# ---------------------------------------------------------------------------
# 1. TinyDB — Bloom Filter (line plot, log Y)
# ---------------------------------------------------------------------------

def _plot_tinydb_grouped_bars(data: dict, title: str, out_filename: str) -> None:
    scales = data["scales"]
    labels = [f"{s['num_docs']:,}" for s in scales]
    base_mean = [s["baseline_mean_ms"] for s in scales]
    base_std = [s["baseline_std_ms"] for s in scales]
    exp_mean = [s["optimized_mean_ms"] for s in scales]
    exp_std = [s["optimized_std_ms"] for s in scales]

    x = np.arange(len(labels))
    width = 0.32

    fig, ax = plt.subplots(figsize=(9, 5.3))
    bars_base = ax.bar(
        x - width / 2,
        base_mean,
        width,
        yerr=base_std,
        capsize=5,
        label="Baseline",
        color=PALETTE["Baseline"],
        edgecolor="white",
    )
    bars_exp = ax.bar(
        x + width / 2,
        exp_mean,
        width,
        yerr=exp_std,
        capsize=5,
        label="Experimento",
        color=PALETTE["Experimento"],
        edgecolor="white",
    )

    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Número de documentos")
    ax.set_ylabel("Tempo médio (ms) — escala log")
    ax.set_title(title)
    ax.legend()

    for bar, s in zip(bars_exp, scales):
        ax.annotate(
            f"−{s['improvement_pct']:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color=PALETTE["Experimento"],
        )

    savefig(fig, os.path.join(PLOTS, "tinydb", out_filename))


def plot_tinydb_bloom_filter() -> None:
    print("Plotting: TinyDB Bloom Filter")
    path = os.path.join(RESULTS, "tinydb", "result_tinydb_bloom-filter.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    _plot_tinydb_grouped_bars(data, "TinyDB: Bloom Filter", "tinydb_bloom_filter_comparison.png")


def plot_tinydb_btree() -> None:
    print("Plotting: TinyDB B-Tree")
    path = os.path.join(RESULTS, "tinydb", "result_tinydb_btree.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    _plot_tinydb_grouped_bars(data, "TinyDB: B-Tree", "tinydb_btree_comparison.png")


# ---------------------------------------------------------------------------
# 2 & 3. python-dotenv — ChainMap (sem interpolação e com interpolação)
# ---------------------------------------------------------------------------

def _plot_chainmap(json_filename: str, title_suffix: str, out_filename: str) -> None:
    path = os.path.join(RESULTS, "python-dotenv", json_filename)
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    num_vars   = [d["num_variables"]           for d in data]
    base_mean = [d["baseline"]["mean_ms"] for d in data]
    base_std = [d["baseline"]["std_ms"] for d in data]
    exp_mean = [d["optimized"]["mean_ms"] for d in data]
    exp_std = [d["optimized"]["std_ms"] for d in data]

    fig, ax = plt.subplots(figsize=(10.5, 5.2))

    ax.errorbar(
        num_vars,
        base_mean,
        yerr=base_std,
        label="Baseline",
        color=PALETTE["Baseline"],
        linewidth=1.8,
        alpha=0.9,
        capsize=3,
    )
    ax.errorbar(
        num_vars,
        exp_mean,
        yerr=exp_std,
        label="Experimento",
        color=PALETTE["Experimento"],
        linewidth=1.8,
        alpha=0.9,
        capsize=3,
    )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Número de variáveis de ambiente")
    ax.set_ylabel("Tempo médio (ms) — escala log")
    ax.set_title(f"python-dotenv: ChainMap {title_suffix}")
    ax.legend()

    savefig(fig, os.path.join(PLOTS, "python-dotenv", out_filename))


def plot_dotenv_chainmap_no_interp() -> None:
    print("Plotting: python-dotenv ChainMap (sem interpolação)")
    _plot_chainmap(
        "result_no_interpolation_dotenv_chainmap.json",
        "(sem interpolação)",
        "dotenv_chainmap_no_interpolation.png",
    )


def plot_dotenv_chainmap_interp() -> None:
    print("Plotting: python-dotenv ChainMap (com interpolação)")
    _plot_chainmap(
        "result_interpolation_dotenv_chainmap.json",
        "(com interpolação)",
        "dotenv_chainmap_interpolation.png",
    )


# ---------------------------------------------------------------------------
# 4. python-dotenv — str.count newline (barplot)
# ---------------------------------------------------------------------------

def plot_dotenv_str_count() -> None:
    print("Plotting: python-dotenv str.count newline")
    path = os.path.join(RESULTS, "python-dotenv",
                        "result_python-dotenv_str-count-newline-advance.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    labels = ["Baseline", "Experimento"]
    means  = [data["baseline"]["mean_ms"], data["optimized"]["mean_ms"]]
    stds   = [data["baseline"]["std_ms"],  data["optimized"]["std_ms"]]
    colors = [PALETTE["Baseline"], PALETTE["Experimento"]]

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    bars = ax.bar(labels, means, yerr=stds, capsize=6,
                  color=colors, width=0.32, edgecolor="white")

    ax.set_ylim(0, max(m + s for m, s in zip(means, stds)) * 1.28)

    ax.set_ylabel("Tempo médio (ms)")
    ax.set_title("python-dotenv: str.count newline")

    savefig(fig, os.path.join(PLOTS, "python-dotenv", "dotenv_str_count_newline.png"))


# ---------------------------------------------------------------------------
# Helper: generic single-comparison barplot for whoosh experiments
# ---------------------------------------------------------------------------

def _plot_whoosh_barplot(
    data: dict,
    title: str,
    out_path: str,
) -> None:
    labels = ["Baseline", "Experimento"]
    means  = [data["baseline"]["mean_ms"],  data["optimized"]["mean_ms"]]
    stds   = [data["baseline"]["std_ms"],   data["optimized"]["std_ms"]]
    colors = [PALETTE["Baseline"], PALETTE["Experimento"]]

    confirmed = data.get("improvement_confirmed", False)
    improvement = data.get("improvement_pct", 0.0) or 0.0

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    bars = ax.bar(labels, means, yerr=stds, capsize=6,
                  color=colors, width=0.32, edgecolor="white")

    ax.set_ylim(0, max(m + s for m, s in zip(means, stds)) * 1.30)

    ax.set_ylabel("Tempo médio (ms)")
    ax.set_title(title)

    savefig(fig, out_path)


# ---------------------------------------------------------------------------
# 5. Whoosh — Skip Lists
# ---------------------------------------------------------------------------

def plot_whoosh_skip_lists() -> None:
    print("Plotting: Whoosh Skip Lists")
    path = os.path.join(RESULTS, "whoosh-reloaded",
                        "result_whoosh-reloaded_skip-lists.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    _plot_whoosh_barplot(
        data,
        "Whoosh-Reloaded: Skip Lists",
        os.path.join(PLOTS, "whoosh-reloaded", "whoosh_skip_lists_comparison.png"),
    )


# ---------------------------------------------------------------------------
# 6. Whoosh — Bloom Filter negative lookup
# ---------------------------------------------------------------------------

def plot_whoosh_bloom_filter() -> None:
    print("Plotting: Whoosh Bloom Filter")
    path = os.path.join(RESULTS, "whoosh-reloaded",
                        "result_whoosh-reloaded_bloom-filter.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    _plot_whoosh_barplot(
        data,
        "Whoosh-Reloaded: Bloom Filter",
        os.path.join(PLOTS, "whoosh-reloaded", "whoosh_bloom_filter_comparison.png"),
    )


# ---------------------------------------------------------------------------
# 7. Whoosh — N-gramas
# ---------------------------------------------------------------------------

def plot_whoosh_ngrams() -> None:
    print("Plotting: Whoosh N-gramas")
    path = os.path.join(RESULTS, "whoosh-reloaded",
                        "result_whoosh-reloaded_ngrams.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    _plot_whoosh_barplot(
        data,
        "Whoosh-Reloaded: N-grams",
        os.path.join(PLOTS, "whoosh-reloaded", "whoosh_ngrams_comparison.png"),
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    plot_tinydb_bloom_filter()
    plot_tinydb_btree()
    plot_dotenv_chainmap_no_interp()
    plot_dotenv_chainmap_interp()
    plot_dotenv_str_count()
    plot_whoosh_skip_lists()
    plot_whoosh_bloom_filter()
    plot_whoosh_ngrams()
    print("\nDone. All plots saved.")


if __name__ == "__main__":
    main()
