import os
import time
from logging import getLogger, StreamHandler, DEBUG, FileHandler

from dotenv import load_dotenv

from news_feeder import get_updated_articles, save_new_article_url
from truth_social import compose_truth

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler2 = FileHandler(filename="/proc/1/fd/1")
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.addHandler(handler2)
logger.propagate = False

load_dotenv()  # take environment variables from .env.

WEB_RSS_URL = "http://feeds.bbci.co.uk/japanese/rss.xml"
WEB_PREVIOUS_URL_FILE = "data_files/bbc_web_previous_url.txt"

YOUTUBE_RSS_URL = (
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCCcey5CP5GDZeom987gqTdg"
)
YOUTUBE_PREVIOUS_URL_FILE = "data_files/bbc_youtube_previous_url.txt"

BBC_USERNAME = os.getenv("BBC_TRUTHSOCIAL_USERNAME")
BBC_PASSWORD = os.getenv("BBC_TRUTHSOCIAL_PASSWORD")
BBC_TOKEN = os.getenv("BBC_TRUTHSOCIAL_TOKEN")


def publish():
    # web
    web_updated_articles = get_updated_articles(WEB_RSS_URL, WEB_PREVIOUS_URL_FILE)

    if not web_updated_articles:
        logger.debug("no article (bbc web)")
        return

    for article in web_updated_articles:
        logger.debug(f"bbc web: {article.title}")
        content = f"{article.title}\n{article.link}\n#inkei_news"
        compose_truth(BBC_USERNAME, BBC_PASSWORD, BBC_TOKEN, content)

        # 成功したら投稿済みurlとして保存.
        save_new_article_url(article.link, WEB_PREVIOUS_URL_FILE)

        time.sleep(10)

    # youtube
    youtube_updated_articles = get_updated_articles(
        YOUTUBE_RSS_URL, YOUTUBE_PREVIOUS_URL_FILE
    )

    if not youtube_updated_articles:
        logger.debug("no article (bbc youtube)")

    for article in youtube_updated_articles:
        logger.debug(f"bbc youtube: {article.title}")
        content = f"{article.title}\n{article.link}\n#inkei_news"
        compose_truth(BBC_USERNAME, BBC_PASSWORD, BBC_TOKEN, content)

        # 成功したら投稿済みurlとして保存.
        save_new_article_url(article.link, YOUTUBE_PREVIOUS_URL_FILE)

        time.sleep(10)


if __name__ == "__main__":
    publish()
