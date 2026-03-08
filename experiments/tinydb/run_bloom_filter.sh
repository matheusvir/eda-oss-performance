#!/bin/bash
set -e

echo "Building Docker image..."
docker build -t tinydb-perf ./setup/tinydb/

echo "Running bloom filter benchmark..."
echo "This will test get(doc_id) and contains(doc_id) with 1K, 10K, and 100K docs"
echo "50 runs per scenario, discarding first 10 and last 10 (30 effective runs)"
echo ""

docker run --rm \
  -v "$(pwd)":/app \
  -e PYTHONPATH=/app/tinydb \
  tinydb-perf \
  python /app/experiments/tinydb/benchmark_bloom_filter.py
