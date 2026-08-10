# truth news bot

## setup

### installation

```bash
  poetry install
```

### set environment variables

``` bash
TEST_TRUTHSOCIAL_USERNAME=foo
TEST_TRUTHSOCIAL_PASSWORD=bar
NHK_TRUTHSOCIAL_USERNAME=foo
NHK_TRUTHSOCIAL_PASSWORD=bar
ASAHI_SANKEI_TRUTHSOCIAL_USERNAME=foo
ASAHI_SANKEI_TRUTHSOCIAL_PASSWORD=bar

```

## usage

- run

```bash
docker compose up -d --build
```

- log

```bash
docker logs truth-bot --tail=100
```

- reset url data

```bash
docker exec -d truth-bot poetry run python -u initialize.py
```

- clean up old data

```bash
docker exec -d truth-bot poetry run python -u clean.py
```

## logs

Log format is `<date> <time> JST <LEVEL> <module> <message>`.

Two things to know before filtering:

- **Publish failures are `WARNING`, not `ERROR`.** `ERROR` appears only once retries are
  exhausted (`Max retry exceeded`). RSS feed problems are `WARNING` too. Filtering on
  `ERROR` alone hides most of what matters.
- **`2>&1` is required** — `docker logs` writes to stderr. Anchor the pattern on `JST `
  so it matches the level field, not the word "error" inside a message or article title.

- errors and warnings (the usual one)

```bash
docker logs truth-bot 2>&1 | grep -E "JST (ERROR|WARNING|CRITICAL)"
```

- errors only

```bash
docker logs truth-bot 2>&1 | grep -E "JST (ERROR|CRITICAL)"
```

- follow live (`--line-buffered` keeps the pipe from lagging)

```bash
docker logs -f truth-bot 2>&1 | grep --line-buffered -E "JST (ERROR|WARNING|CRITICAL)"
```

- with traceback — `RSS check failed` logs a traceback whose continuation lines have no
  level prefix, so plain grep shows only the first line

```bash
docker logs truth-bot 2>&1 | grep -A 15 -E "JST (ERROR|CRITICAL)"
```

- tally what happened in the last day

```bash
docker logs truth-bot --since 24h 2>&1 \
  | grep -oE "Publish failed|Max retry exceeded|RSS check failed|RSS fetch failed|RSS returned no entries|Skipped [0-9]+ entries" \
  | sort | uniq -c
```

- read everything without the truthbrush noise — `truthbrush.api:_post` dumps the full
  response (~5 KB) on every post

```bash
docker logs truth-bot --tail=200 2>&1 | grep -v "truthbrush.api:_post"
```

Note that `truthbrush` logs through loguru in **UTC**, while the app logs in **JST**.
The same event appears with timestamps 9 hours apart.

## References

- The connection process to Truth social is based on the following repository
    - https://github.com/stanfordio/truthbrush
- https://pypi.org/project/feedparser/
- https://truthsocial.com/
