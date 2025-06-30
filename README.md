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
docker exec -d truth-bot poetry run python -u main.py
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

## References

- The connection process to Truth social is based on the following repository
    - https://github.com/stanfordio/truthbrush
- https://pypi.org/project/feedparser/
- https://truthsocial.com/
