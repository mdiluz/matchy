#!/usr/bin/env bash
set -x
set -e

# Check formatting and linting
flake8 --max-line-length 120 $(git ls-files '*.py')

# Run pytest
pytest