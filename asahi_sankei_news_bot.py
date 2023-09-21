import time
import os
from news_feeder import get_updated_articles
from truth_social import compose_truth
from logging import getLogger, StreamHandler, DEBUG, FileHandler
from dotenv import load_dotenv

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler2 = FileHandler(filename="/proc/1/fd/1")
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.addHandler(handler2)
logger.propagate = False

load_dotenv()  # take environment variables from .env.

ASAHI_RSS_URL = "https://www.asahi.com/rss/asahi/newsheadlines.rdf"
ASAHI_PREVIOUS_URL_FILE = "data_files/asahi_previous_url.txt"
SANKEI_RSS_URL = "https://assets.wor.jp/rss/rdf/sankei/flash.rdf"
SANKEI_PREVIOUS_URL_FILE = "data_files/sankei_previous_url.txt"

ASAHI_SANKEI_USERNAME = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_USERNAME")
ASAHI_SANKEI_PASSWORD = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_PASSWORD")
ASAHI_SANKEI_TOKEN = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_TOKEN")


def publish():
    asahi_updated_articles = get_updated_articles(
        ASAHI_RSS_URL, ASAHI_PREVIOUS_URL_FILE
    )

    if not asahi_updated_articles:
        logger.debug("no article (asahi)")

    for article in asahi_updated_articles:
        if article.title.startswith("【"):
            continue

        logger.debug(f"asahi: {article.title}")
        content = f"{article.title}\n{article.link}\n#inkei_news"
        compose_truth(
            ASAHI_SANKEI_USERNAME, ASAHI_SANKEI_PASSWORD, ASAHI_SANKEI_TOKEN, content
        )
        time.sleep(10)

    sankei_updated_articles = get_updated_articles(
        SANKEI_RSS_URL, SANKEI_PREVIOUS_URL_FILE
    )

    if not sankei_updated_articles:
        logger.debug("no article (sankei)")

    for article in sankei_updated_articles:
        if article.title.startswith("【"):
            continue

        logger.debug(f"sankei: {article.title}")
        content = f"{article.title}\n{article.link}\n#inkei_news"
        compose_truth(
            ASAHI_SANKEI_USERNAME, ASAHI_SANKEI_PASSWORD, ASAHI_SANKEI_TOKEN, content
        )
        time.sleep(10)


if __name__ == "__main__":
    publish()
