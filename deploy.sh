#!/bin/bash
# Build, QA, legal gate, then commit. Usage: ./deploy.sh [--launch] "commit message"
set -e
cd "$(dirname "$0")"
MODE=""
if [ "$1" = "--launch" ]; then MODE="--launch"; shift; fi
python3 _build/build.py $MODE
python3 _build/check.py $MODE
python3 _build/legal_gate.py check || { echo "LEGAL GATE HOLD: not deploying"; exit 3; }
echo "build ok ($MODE)"
