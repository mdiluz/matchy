#!/usr/bin/env bash
set -x
set -e

while python matchy.py
do
    git fetch
    git checkout validated
done
