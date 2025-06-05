from typing import List

import feedparser

from models import Article


def get_articles(url: str) -> List[Article]:
    """
    更新された記事を取得.
    """
    # rssのurlから記事取得
    rss_data = feedparser.parse(url)
    rss_entries = rss_data.entries

    return [Article(entry.title, entry.link) for entry in rss_entries]
