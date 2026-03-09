#!/usr/bin/env bash
# Run bloom filter benchmark: baseline (pure whoosh) then experiment (bloom-optimized).
#
# Isolation strategy: the whoosh-reloaded submodule is checked out to
# different git refs before each Docker build, so the baseline image
# contains vanilla whoosh and the experiment image contains only the
# bloom filter optimization (no skip-lists or n-grams).
#
# Refs:
#   Baseline  — da74c780  (last pure upstream commit)
#   Experiment — temp-bloom-only  (bloom filter cherry-picked onto pure)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SUBMODULE_DIR="${REPO_ROOT}/whoosh-reloaded"

IMAGE_BASELINE="eda-whoosh-bloom-baseline"
IMAGE_EXPERIMENT="eda-whoosh-bloom-experiment"
RESULTS_DIR="${REPO_ROOT}/results/whoosh-reloaded"
RESULT_JSON="/results/result_whoosh-reloaded_bloom-filter.json"

BASELINE_REF="da74c780"
EXPERIMENT_REF="temp-bloom-only"

# Save current submodule ref so we can restore it at the end
ORIGINAL_REF="$(git -C "${SUBMODULE_DIR}" rev-parse HEAD)"

cleanup() {
    echo "Restoring submodule to original ref (${ORIGINAL_REF})..."
    git -C "${SUBMODULE_DIR}" checkout --quiet "${ORIGINAL_REF}" 2>/dev/null || true
}
trap cleanup EXIT

# ── Baseline build ──────────────────────────────────────────────────
echo "=== Checking out baseline ref (${BASELINE_REF}) ==="
git -C "${SUBMODULE_DIR}" fetch --all --quiet
git -C "${SUBMODULE_DIR}" checkout --quiet "${BASELINE_REF}"

echo "=== Building baseline Docker image ==="
docker build \
  --file "${REPO_ROOT}/setup/whoosh-reloaded/Dockerfile" \
  --tag "${IMAGE_BASELINE}" \
  "${REPO_ROOT}"

# ── Experiment build ────────────────────────────────────────────────
echo "=== Checking out experiment ref (${EXPERIMENT_REF}) ==="
git -C "${SUBMODULE_DIR}" checkout --quiet "${EXPERIMENT_REF}"

echo "=== Building experiment Docker image ==="
docker build \
  --file "${REPO_ROOT}/setup/whoosh-reloaded/Dockerfile" \
  --tag "${IMAGE_EXPERIMENT}" \
  "${REPO_ROOT}"

# ── Run benchmarks ──────────────────────────────────────────────────
mkdir -p "${RESULTS_DIR}"

echo "=== Running baseline benchmark ==="
docker run --rm \
  -v "${RESULTS_DIR}:/results" \
  "${IMAGE_BASELINE}" \
  python experiments/baseline_whoosh-reloaded_bloom-filter.py \
    --output "${RESULT_JSON}" \
    "$@"

echo "=== Running experiment benchmark ==="
docker run --rm \
  -v "${RESULTS_DIR}:/results" \
  "${IMAGE_EXPERIMENT}" \
  python experiments/experiment_whoosh-reloaded_bloom-filter.py \
    --output "${RESULT_JSON}" \
    --baseline "${RESULT_JSON}" \
    "$@"

echo "=== Done. Results at: ${RESULTS_DIR}/result_whoosh-reloaded_bloom-filter.json ==="
