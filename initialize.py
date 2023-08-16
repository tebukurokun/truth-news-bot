from typing import List, Set
from dataclasses import dataclass
import feedparser

from nhk_news_feed import save_article_urls

NHK_RSS_URL = 'https://www3.nhk.or.jp/rss/news/cat0.xml'
NHK_PREVIOUS_URL_FILE = 'data_files/nhk_previous_url.txt'
ASAHI_RSS_URL = 'https://www.asahi.com/rss/asahi/newsheadlines.rdf'
ASAHI_PREVIOUS_URL_FILE = 'data_files/asahi_previous_url.txt'
SANKEI_RSS_URL = 'https://assets.wor.jp/rss/rdf/sankei/flash.rdf'
SANKEI_PREVIOUS_URL_FILE = 'data_files/sankei_previous_url.txt'


def initialize_previous_url(rss_url: str, file: str):
    # rssのurlから記事取得
    rss_data = feedparser.parse(rss_url)
    rss_entries = rss_data.entries
    urls = [entry.link for entry in rss_entries]

    save_article_urls(urls, file)


if __name__ == '__main__':
    initialize_previous_url(NHK_RSS_URL, NHK_PREVIOUS_URL_FILE)
    initialize_previous_url(ASAHI_RSS_URL,ASAHI_PREVIOUS_URL_FILE)
    initialize_previous_url(SANKEI_RSS_URL, SANKEI_PREVIOUS_URL_FILE)
