import threading
from typing import Dict, Tuple

from dotenv import load_dotenv

from truthbrush.api import Api

load_dotenv()  # take environment variables from .env.

# Api は失効したトークンを取り直して保持するので、投稿ごとに作り直さず
# 認証情報ごとに使い回す。毎回作り直すと、env のトークンが失効したあと
# 投稿のたびに OAuth ログインが走ることになる。
_api_cache: Dict[Tuple[str, str, str], Api] = {}
_api_cache_lock = threading.Lock()


def _get_api(username: str, password: str, token: str) -> Api:
    key = (username, password, token)

    with _api_cache_lock:
        api = _api_cache.get(key)
        if api is None:
            api = Api(username, password, token)
            _api_cache[key] = api

    return api


def compose_truth(username: str, password: str, token: str, message: str):
    """Compose Truth."""

    _get_api(username, password, token).compose_truth(message)
