import os
import time
from logging import getLogger, StreamHandler, DEBUG, FileHandler

from dotenv import load_dotenv

from news_feeder import get_updated_articles, save_new_article_urls
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

RSS_URL = "http://feeds.cnn.co.jp/rss/cnn/cnn.rdf"
PREVIOUS_URL_FILE = "data_files/cnn_previous_url.txt"

CNN_USERNAME = os.getenv("CNN_TRUTHSOCIAL_USERNAME")
CNN_PASSWORD = os.getenv("CNN_TRUTHSOCIAL_PASSWORD")
CNN_TOKEN = os.getenv("CNN_TRUTHSOCIAL_TOKEN")


def publish():
    updated_articles = get_updated_articles(RSS_URL, PREVIOUS_URL_FILE)

    if not updated_articles:
        logger.debug("no article (cnn)")

    for article in updated_articles:
        logger.debug(f"cnn: {article.title}")
        content = f"{article.title}\n{article.link}\n#inkei_news"
        compose_truth(CNN_USERNAME, CNN_PASSWORD, CNN_TOKEN, content)
        time.sleep(10)

    # 成功したら投稿済みurlとして保存.
    save_new_article_urls(
        [article.link for article in updated_articles], PREVIOUS_URL_FILE
    )


if __name__ == "__main__":
    publish()
