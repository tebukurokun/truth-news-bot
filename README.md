# truth news bot

## setup

### installation
```bash
  poetry install
```

### set environment variables
``` bash
TRUTHSOCIAL_USERNAME=foo
TRUTHSOCIAL_PASSWORD=bar
```

## usage
```bash
docker compose up -d --build
docker exec truth-bot python -u nhk_news_bot.py
```


## References
- The connection process to Truth social is based on the following repository
  - https://github.com/stanfordio/truthbrush
- https://pypi.org/project/feedparser/
- https://truthsocial.com/
