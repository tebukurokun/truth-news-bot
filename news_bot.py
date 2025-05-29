import os
import time
from logging import getLogger, StreamHandler, DEBUG, FileHandler
import random
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


NHK_RSS_URL = "https://www3.nhk.or.jp/rss/news/cat0.xml"
NHK_PREVIOUS_URL_FILE = "data_files/nhk_previous_url.txt"
NHK_USERNAME = os.getenv("NHK_TRUTHSOCIAL_USERNAME")
NHK_PASSWORD = os.getenv("NHK_TRUTHSOCIAL_PASSWORD")
NHK_TOKEN = os.getenv("NHK_TRUTHSOCIAL_TOKEN")

ASAHI_RSS_URL = "https://www.asahi.com/rss/asahi/newsheadlines.rdf"
ASAHI_PREVIOUS_URL_FILE = "data_files/asahi_previous_url.txt"
SANKEI_RSS_URL = "https://assets.wor.jp/rss/rdf/sankei/flash.rdf"
SANKEI_PREVIOUS_URL_FILE = "data_files/sankei_previous_url.txt"
ASAHI_SANKEI_USERNAME = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_USERNAME")
ASAHI_SANKEI_PASSWORD = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_PASSWORD")
ASAHI_SANKEI_TOKEN = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_TOKEN")


def publish():
    nhk_updated_articles = (lambda x: random.sample(x, min(2, len(x))))(
        get_updated_articles(NHK_RSS_URL, NHK_PREVIOUS_URL_FILE)
    )

    asahi_sankei_updated_articles = (lambda x: random.sample(x, min(2, len(x))))(
        get_updated_articles(ASAHI_RSS_URL, ASAHI_PREVIOUS_URL_FILE)
        + get_updated_articles(SANKEI_RSS_URL, SANKEI_PREVIOUS_URL_FILE)
    )

    if not nhk_updated_articles and not asahi_sankei_updated_articles:
        logger.debug("no article (nhk, asahi, sankei)")
        return

    for article in nhk_updated_articles:
        content = f"{article.title}\n{article.link}\n#nhk_news #inkei_news"

        try:
            compose_truth(NHK_USERNAME, NHK_PASSWORD, NHK_TOKEN, content)
            save_new_article_url(article.link, NHK_PREVIOUS_URL_FILE)
            logger.info(f"Posted NHK article: {article.title}")

        except Exception as e:
            logger.error(f"Failed NHK article: {article.title}\n {e}")
            continue
        finally:
            time.sleep(10)

    for article in asahi_sankei_updated_articles:
        content = f"{article.title}\n{article.link}\n#nhk_news #inkei_news"

        try:
            compose_truth(NHK_USERNAME, NHK_PASSWORD, NHK_TOKEN, content)
            save_new_article_url(article.link, NHK_PREVIOUS_URL_FILE)
            logger.info(f"Posted asahi sankei article: {article.title}")

        except Exception as e:
            logger.error(f"Failed asahi sankei article: {article.title}\n {e}")
            continue
        finally:
            time.sleep(10)


if __name__ == "__main__":
    publish()
