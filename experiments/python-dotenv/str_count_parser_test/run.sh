#!/bin/bash
# run.sh — str_count_parser_test benchmark
# Runs either the baseline or experiment script depending on the VARIANT env var.
# Usage:
#   docker run -e VARIANT=baseline ...
#   docker run -e VARIANT=optimized ...

set -e

VARIANT=${VARIANT:-"baseline"}
EXPERIMENTS_DIR="/workspace/experiments/str_count_parser_test"

echo "========================================"
echo "Benchmark: str-count-newline-advance"
echo "Variant: $VARIANT"
echo "========================================"

if [ "$VARIANT" = "baseline" ]; then
    echo "Running baseline (re.findall)..."
    python "$EXPERIMENTS_DIR/baseline_pythondotenv_str-count-newline-advance.py"

elif [ "$VARIANT" = "optimized" ]; then
    echo "Running experiment (str.count)..."
    python "$EXPERIMENTS_DIR/experiment_pythondotenv_str-count-newline-advance.py"

else
    echo "Unknown VARIANT: $VARIANT"
    echo "Use VARIANT=baseline or VARIANT=optimized"
    exit 1
fi

echo "========================================"
echo "Done."
echo "========================================"
