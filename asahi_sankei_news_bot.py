import os
import random
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

ASAHI_RSS_URL = "https://www.asahi.com/rss/asahi/newsheadlines.rdf"
ASAHI_PREVIOUS_URL_FILE = "data_files/asahi_previous_url.txt"
SANKEI_RSS_URL = "https://assets.wor.jp/rss/rdf/sankei/flash.rdf"
SANKEI_PREVIOUS_URL_FILE = "data_files/sankei_previous_url.txt"

ASAHI_SANKEI_USERNAME = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_USERNAME")
ASAHI_SANKEI_PASSWORD = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_PASSWORD")
ASAHI_SANKEI_TOKEN = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_TOKEN")


def publish():
    # asahi
    asahi_updated_articles = get_updated_articles(
        ASAHI_RSS_URL, ASAHI_PREVIOUS_URL_FILE
    )

    if not asahi_updated_articles:
        logger.debug("no article (asahi)")

    # sankei
    sankei_updated_articles = get_updated_articles(
        SANKEI_RSS_URL, SANKEI_PREVIOUS_URL_FILE
    )

    if not sankei_updated_articles:
        logger.debug("no article (sankei)")

    if not asahi_updated_articles and not sankei_updated_articles:
        return

    updated_articles = asahi_updated_articles + sankei_updated_articles
    sampled_articles = random.sample(updated_articles, min(4, len(updated_articles)))

    for article in sampled_articles:
        previous_url_file = ASAHI_PREVIOUS_URL_FILE if 'asahi.com' in article.link else SANKEI_PREVIOUS_URL_FILE

        if article.title.startswith("【"):
            # "【" のときも投稿済みurlとして保存.
            save_new_article_url(article.link, previous_url_file)
            continue

        logger.debug(f"asahi_sankei: {article.title}")
        content = f"{article.title}\n{article.link}\n#inkei_news"
        try:
            compose_truth(
                ASAHI_SANKEI_USERNAME, ASAHI_SANKEI_PASSWORD, ASAHI_SANKEI_TOKEN, content
            )
            # 成功したら投稿済みurlとして保存.
            save_new_article_url(article.link, previous_url_file)

        except Exception as e:
            logger.error(f"Failed to post article: {e}")
            continue
        finally:
            time.sleep(10)


if __name__ == "__main__":
    publish()
