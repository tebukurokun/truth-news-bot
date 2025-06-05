import feedparser

from service.url_manager import URLManager

NHK_RSS_URL = "https://www3.nhk.or.jp/rss/news/cat0.xml"
ASAHI_RSS_URL = "https://www.asahi.com/rss/asahi/newsheadlines.rdf"
SANKEI_RSS_URL = "https://assets.wor.jp/rss/rdf/sankei/flash.rdf"
BBC_WEB_RSS_URL = "http://feeds.bbci.co.uk/japanese/rss.xml"
BBC_YOUTUBE_RSS_URL = (
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCCcey5CP5GDZeom987gqTdg"
)
CNN_RSS_URL = "http://feeds.cnn.co.jp/rss/cnn/cnn.rdf"
NIKKEI_RSS_URL = "https://assets.wor.jp/rss/rdf/nikkei/news.rdf"
GUARDIAN_RSS_URL = "https://www.theguardian.com/international/rss"


# URLManager初期化
url_manager = URLManager()


def initialize_previous_url(rss_url: str):
    # rssのurlから記事取得
    rss_data = feedparser.parse(rss_url)
    rss_entries = rss_data.entries

    for entry in rss_entries:
        url_manager.add_url(entry.link, entry.title)


def initialize_previous_urls():
    """
    各RSSの最新記事のURLを取得し、前回のURLファイルを初期化する.
    """
    initialize_previous_url(NHK_RSS_URL)
    initialize_previous_url(ASAHI_RSS_URL)
    initialize_previous_url(SANKEI_RSS_URL)
    initialize_previous_url(BBC_WEB_RSS_URL)
    initialize_previous_url(BBC_YOUTUBE_RSS_URL)
    initialize_previous_url(CNN_RSS_URL)
    initialize_previous_url(NIKKEI_RSS_URL)
    initialize_previous_url(GUARDIAN_RSS_URL)


if __name__ == "__main__":
    initialize_previous_urls()
