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

# optional
NTFY_URL=https://ntfy.sh/<topic>   # error notifications (see "error notifications")
NTFY_COOLDOWN_SECONDS=1800
LOG_LEVEL=INFO
MAX_RETRY=10

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

## error notifications

`ERROR` and `CRITICAL` logs are pushed to [ntfy](https://ntfy.sh) so that a broken bot does
not sit unnoticed until someone reads `docker logs`. `utils/notifier.py` attaches an
`NtfyHandler` to every logger built by `setup_logger`.

Set the topic URL in `production.env` — **the topic name is the only secret protecting it,
so keep it out of git**:

```bash
NTFY_URL=https://ntfy.sh/<topic>
```

Without `NTFY_URL` nothing is sent, which is the default for local development.
Subscribe from the ntfy app or with `curl -s https://ntfy.sh/<topic>/json`.

What gets pushed:

- `Max retry exceeded` — an article failed `MAX_RETRY` times and was dropped. An expired
  token that cannot be refreshed shows up here, roughly `MAX_RETRY * 11` seconds after the
  first failure.
- `RSS check failed` — the RSS thread raised, traceback included in the body.
- any other `ERROR` / `CRITICAL` from the app loggers.

Per-post `WARNING`s (`Publish failed`) are **not** pushed; they are normal and transient.

Notifications are throttled per error kind (the text before the first `:`), one every
`NTFY_COOLDOWN_SECONDS` (default 1800). Suppressed occurrences are counted and reported in
the next notification of that kind — otherwise an expired token would fire one push per
article. Sending is capped at a 5 s timeout and never raises: if ntfy is down, the bot
keeps posting and only the notification is lost.

## posting: why the response body is checked, not the status code

**Truth Social answers `POST /api/v1/statuses` with `200 OK` even when the bearer token has
expired.** The status code, `ok`, and `reason` all look fine; only the body differs. So
`resp.raise_for_status()` is not enough — `compose_truth` in `truthbrush/api.py` decides
success by looking for the id of the created status (`_is_created_status`).

- success — the created Status object, ~1.3 KB

```json
{"created_at":"2026-08-17T07:32:19.029Z","id":"117109682276175607","url":"https://truthsocial.com/@.../117109682276175607", ...}
```

- expired token — `200 OK`, empty object, `content-length: 28`

```json
{}
```

Do not relax this check back to a status-code-only one. When a post silently "succeeds",
`_post_and_save` in `news_bot.py` records the URL as published, and the article is never
posted again.

On an id-less response, `compose_truth` re-runs the OAuth login (when
`<MEDIA>_TRUTHSOCIAL_USERNAME` / `_PASSWORD` are set) and retries the post once, so an
expired `<MEDIA>_TRUTHSOCIAL_TOKEN` recovers by itself. `service/truth_social.py` keeps one
`Api` instance per credential set so the refreshed token survives across posts. Accounts
configured with a token only cannot re-login — they fail with `PostErrorException` after
`MAX_RETRY` and need the token updated in `production.env`.

To see it happen:

```bash
docker logs truth-bot 2>&1 | grep -E "compose_truth returned no status id|Re-authenticated|created no status"
```

## References

- The connection process to Truth social is based on the following repository
    - https://github.com/stanfordio/truthbrush
- https://pypi.org/project/feedparser/
- https://truthsocial.com/
