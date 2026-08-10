#!/bin/bash
set -euo pipefail

docker exec truth-bot poetry run python -u clean.py
