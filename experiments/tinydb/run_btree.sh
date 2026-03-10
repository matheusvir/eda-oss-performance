#!/bin/bash
set -e

echo "Building Docker image..."
docker build -t tinydb-perf ./setup/tinydb/

echo "Running B-Tree benchmark..."
docker run --rm \
  -v "$(pwd)":/app \
  -e PYTHONPATH=/app/tinydb \
  tinydb-perf \
  python /app/experiments/tinydb/benchmark_btree.py
