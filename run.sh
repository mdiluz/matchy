#!/usr/bin/env bash
set -x
set -e

source .venv/bin/activate

while python matchy.py
do
    git pull
    python -m pip install -r requirements.txt
done
