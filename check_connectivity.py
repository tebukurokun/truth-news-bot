"""サーバー移転前の疎通確認.

RSS / Truth Social / ntfy に届くかを確認する。読み取りのみで、投稿も DB への書き込みもしない。

    docker compose run --rm truth-bot poetry run python -u check_connectivity.py

結果は print で出す（logger の ERROR は ntfy に通知されるため使わない）。
NG が 1 つでもあれば exit 1。
"""

import os
import socket
import sys
import urllib.request
from typing import Optional
from urllib.parse import urlsplit

import feedparser
from curl_cffi import requests
from dotenv import load_dotenv

import news_bot
from truthbrush.api import API_BASE_URL, USER_AGENT, Api, proxies

# feedparser は timeout 引数を持たず、既定のソケットタイムアウト（無制限）に従う
socket.setdefaulttimeout(30)

load_dotenv()

RSS_FEEDS = {
    "NHK": news_bot.NHK_RSS_URL,
    "朝日": news_bot.ASAHI_RSS_URL,
    "産経": news_bot.SANKEI_RSS_URL,
    "BBC web": news_bot.BBC_WEB_RSS_URL,
    "BBC YouTube": news_bot.BBC_YOUTUBE_RSS_URL,
    "CNN": news_bot.CNN_RSS_URL,
    "日経": news_bot.NIKKEI_RSS_URL,
}

ACCOUNTS = {
    "NHK": (news_bot.NHK_USERNAME, news_bot.NHK_PASSWORD, news_bot.NHK_TOKEN),
    "朝日・産経": (
        news_bot.ASAHI_SANKEI_USERNAME,
        news_bot.ASAHI_SANKEI_PASSWORD,
        news_bot.ASAHI_SANKEI_TOKEN,
    ),
    "BBC": (news_bot.BBC_USERNAME, news_bot.BBC_PASSWORD, news_bot.BBC_TOKEN),
    "CNN": (news_bot.CNN_USERNAME, news_bot.CNN_PASSWORD, news_bot.CNN_TOKEN),
    "日経": (news_bot.NIKKEI_USERNAME, news_bot.NIKKEI_PASSWORD, news_bot.NIKKEI_TOKEN),
}


def check_rss(url: str) -> Optional[str]:
    """エラー内容を返す。OK なら None."""
    feed = feedparser.parse(url)
    status = feed.get("status")

    if not feed.entries:
        return f"entries=0 status={status} bozo={feed.get('bozo_exception')!r}"

    print(f"    status={status} entries={len(feed.entries)}")
    return None


def check_truth_social(username: str, password: str, token: str) -> Optional[str]:
    """verify_credentials を GET する。投稿 API は叩かない."""
    if not token:
        if not (username and password):
            return "TOKEN も USERNAME/PASSWORD も未設定"
        print("    TOKEN 未設定のため OAuth ログインを試行")
        token = Api(username, password).get_auth_id(username, password)

    # Api._get と同じく curl_cffi で Chrome を装う。レスポンスが JSON とは限らない
    # （Cloudflare に弾かれると HTML が返る）ので、ステータスと本文を自前で見る。
    resp = requests.get(
        API_BASE_URL + "/v1/accounts/verify_credentials",
        proxies=proxies,
        impersonate="chrome110",
        headers={
            "Authorization": "Bearer " + token,
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://truthsocial.com/",
            "Origin": "https://truthsocial.com",
        },
    )

    if "Just a moment" in resp.text[:500]:
        return f"Cloudflare のチャレンジで遮断 (status={resp.status_code})。この IP からは投稿できない可能性が高い"

    if resp.status_code != 200:
        return f"status={resp.status_code} {resp.text[:200]}"

    # 失効トークンでも 200 が返ることがあるので、username が入っているかで判定する
    account = resp.json()
    if not isinstance(account, dict) or not account.get("username"):
        return f"アカウント情報が返らない（トークン失効の可能性）: {resp.text[:200]}"

    print(f"    @{account['username']}")
    return None


def check_ntfy(url: str) -> Optional[str]:
    """ntfy サーバーへの到達性だけを見る（トピック名は表示せず、送信もしない）."""
    parts = urlsplit(url)
    health_url = f"{parts.scheme}://{parts.netloc}/v1/health"

    with urllib.request.urlopen(health_url, timeout=10) as resp:
        print(f"    {parts.netloc} status={resp.status}")

    return None


def run(label: str, func, *args) -> bool:
    print(f"[{label}]")
    try:
        error = func(*args)
    except Exception as e:  # pylint: disable=broad-except
        error = f"{type(e).__name__}: {e}"

    if error:
        print(f"    NG: {error}")
        return False

    print("    OK")
    return True


def main() -> int:
    results = []

    for name, url in RSS_FEEDS.items():
        results.append(run(f"RSS {name}", check_rss, url))

    for name, credentials in ACCOUNTS.items():
        results.append(run(f"Truth Social {name}", check_truth_social, *credentials))

    ntfy_url = os.getenv("NTFY_URL")
    if ntfy_url:
        results.append(run("ntfy", check_ntfy, ntfy_url))
    else:
        print("[ntfy]\n    SKIP: NTFY_URL 未設定")

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
