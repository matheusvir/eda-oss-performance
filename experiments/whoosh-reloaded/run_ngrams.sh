#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

IMAGE_NAME="eda-whoosh-reloaded"
RESULTS_DIR="${REPO_ROOT}/results/whoosh-reloaded"
BASELINE_JSON="/results/result_whoosh-reloaded_ngrams_baseline_only.json"
FINAL_JSON="/results/result_whoosh-reloaded_ngrams.json"

docker build \
  --file "${REPO_ROOT}/setup/whoosh-reloaded/Dockerfile" \
  --tag "${IMAGE_NAME}" \
  "${REPO_ROOT}"

mkdir -p "${RESULTS_DIR}"

docker run --rm \
  -v "${RESULTS_DIR}:/results" \
  "${IMAGE_NAME}" \
  python experiments/baseline_whoosh-reloaded_ngrams.py \
    --output "${BASELINE_JSON}" \
    "$@"

docker run --rm \
  -v "${RESULTS_DIR}:/results" \
  "${IMAGE_NAME}" \
  python experiments/experiment_whoosh-reloaded_ngrams.py \
    --output "${FINAL_JSON}" \
    --baseline "${BASELINE_JSON}" \
    "$@"
