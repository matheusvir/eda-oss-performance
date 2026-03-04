#!/bin/bash

# This script generates multiple .env files and executes load tests.
# It handles both interpolated and non-interpolated configurations.

cd "$(dirname "$0")"
mkdir without_interpolation
mkdir with_interpolation
python3 generate_load.py
python3 run_load_test_no_interpolation.py
python3 run_load_test_interpolation.py