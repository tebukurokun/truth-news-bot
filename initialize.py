from typing import List, Set
from dataclasses import dataclass
import feedparser

from news_feeder import save_new_article_urls

NHK_RSS_URL = "https://www3.nhk.or.jp/rss/news/cat0.xml"
NHK_PREVIOUS_URL_FILE = "data_files/nhk_previous_url.txt"
ASAHI_RSS_URL = "https://www.asahi.com/rss/asahi/newsheadlines.rdf"
ASAHI_PREVIOUS_URL_FILE = "data_files/asahi_previous_url.txt"
SANKEI_RSS_URL = "https://assets.wor.jp/rss/rdf/sankei/flash.rdf"
SANKEI_PREVIOUS_URL_FILE = "data_files/sankei_previous_url.txt"
BBC_WEB_RSS_URL = "http://feeds.bbci.co.uk/japanese/rss.xml"
BBC_WEB_PREVIOUS_URL_FILE = "data_files/bbc_web_previous_url.txt"
BBC_YOUTUBE_RSS_URL = (
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCCcey5CP5GDZeom987gqTdg"
)
BBC_YOUTUBE_PREVIOUS_URL_FILE = "data_files/bbc_youtube_previous_url.txt"
CNN_RSS_URL = "http://feeds.cnn.co.jp/rss/cnn/cnn.rdf"
CNN_PREVIOUS_URL_FILE = "data_files/cnn_previous_url.txt"


def initialize_previous_url(rss_url: str, file: str):
    # rssのurlから記事取得
    rss_data = feedparser.parse(rss_url)
    rss_entries = rss_data.entries
    urls = [entry.link for entry in rss_entries]

    save_new_article_urls(urls, file)


if __name__ == "__main__":
    initialize_previous_url(NHK_RSS_URL, NHK_PREVIOUS_URL_FILE)
    initialize_previous_url(ASAHI_RSS_URL, ASAHI_PREVIOUS_URL_FILE)
    initialize_previous_url(SANKEI_RSS_URL, SANKEI_PREVIOUS_URL_FILE)
    initialize_previous_url(BBC_WEB_RSS_URL, BBC_WEB_PREVIOUS_URL_FILE)
    initialize_previous_url(BBC_YOUTUBE_RSS_URL, BBC_YOUTUBE_PREVIOUS_URL_FILE)
    initialize_previous_url(CNN_RSS_URL, CNN_PREVIOUS_URL_FILE)
