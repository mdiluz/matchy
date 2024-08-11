#!/usr/bin/env bash
set -x
set -e

git pull
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install -r requirements.txt
python matchy.py
