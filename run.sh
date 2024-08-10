#!/usr/bin/env bash
set -x
set -e

while python matchy.py
do
    git pull
done
