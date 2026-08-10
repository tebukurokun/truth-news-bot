#!/bin/bash
set -euo pipefail

cd /home/rocky/truth-news-bot


docker compose stop
docker compose up -d

sleep 5
