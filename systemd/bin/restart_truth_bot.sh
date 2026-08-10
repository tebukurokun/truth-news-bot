#!/bin/bash
set -euo pipefail

cd /home/rocky/truth-news-bot

docker compose stop

# --wait で healthcheck が通るまで待つ。コード変更の反映は伴わない（意図的に --build なし）。
# デプロイは従来どおり手動の `docker compose up -d --build` で行う。
docker compose up -d --wait
