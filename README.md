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
```bash
docker compose up -d --build
docker exec truth-bot python -u initialize.py
docker exec truth-bot python -u nhk_news_bot.py
docker exec truth-bot python -u asahi_sankei_news_bot.py
```


## References
- The connection process to Truth social is based on the following repository
  - https://github.com/stanfordio/truthbrush
- https://pypi.org/project/feedparser/
- https://truthsocial.com/
