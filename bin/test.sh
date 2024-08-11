#!/usr/bin/env bash

# Check formatting and linting
flake8 --max-line-length 120 $(git ls-files '*.py')

# Run pytest
pytest