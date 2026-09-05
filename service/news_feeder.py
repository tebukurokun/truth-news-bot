import calendar
from datetime import datetime, timezone
from typing import List, Optional

import feedparser

from models import Article
from utils import setup_logger

logger = setup_logger(__name__)


def _published_at(entry) -> Optional[datetime]:
    """
    エントリの配信日時を UTC aware な datetime で返す。取れなければ None。

    RSS 1.0 (RDF) の dc:date は published_parsed ではなく updated_parsed に入る。
    朝日・産経・日経はいずれも RDF なので、両方見ないと日時が取れない。
    """
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None

    # *_parsed は UTC の struct_time なので、timegm で UTC として解釈する
    # （mktime だとローカルタイムとして扱われ、時差の分だけずれる）。
    return datetime.fromtimestamp(calendar.timegm(parsed), timezone.utc)


def get_articles(url: str) -> List[Article]:
    """
    更新された記事を取得.

    取得・パースに失敗しても例外は投げずに空リストを返す。
    check_update() は全メディアのフィードを順に処理するため、
    ここで例外を上げると1フィードの障害で全メディアがその巡回ごと止まってしまう。
    代わりに、失敗を「新着なし」と区別できるようログに残す。
    """
    # rssのurlから記事取得
    rss_data = feedparser.parse(url)
    rss_entries = rss_data.entries

    # status はHTTP経由で取得したときのみ存在する
    status = rss_data.get("status")

    if status is not None and status >= 400:
        logger.warning(f"RSS fetch failed: HTTP {status} - {url}")
    elif not rss_entries:
        if rss_data.bozo:
            # ネットワークエラー（タイムアウト等）もここに来る
            logger.warning(
                f"RSS fetch/parse failed: {rss_data.get('bozo_exception')!r} - {url}"
            )
        else:
            logger.warning(f"RSS returned no entries - {url}")
    elif rss_data.bozo:
        # 記事は取れているので異常ではない（名前空間の宣言漏れ等でよく立つ）
        logger.debug(
            f"RSS not well-formed but usable "
            f"({len(rss_entries)} entries): {rss_data.get('bozo_exception')!r} - {url}"
        )

    # 壊れたXMLでも feedparser はエントリを部分的に復元するため、
    # title/link を欠いたエントリが混ざりうる。属性アクセスで落とさない。
    articles = []
    skipped = 0
    for entry in rss_entries:
        title = entry.get("title")
        link = entry.get("link")
        if not title or not link:
            skipped += 1
            continue
        articles.append(Article(title, link, published_at=_published_at(entry)))

    if skipped:
        logger.warning(f"Skipped {skipped} entries missing title/link - {url}")

    return articles
