import time
import os
from news_feeder import get_updated_articles
from truth_social import compose_truth
from logging import getLogger, StreamHandler, DEBUG, FileHandler

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler2 = FileHandler(filename = "/proc/1/fd/1")
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.addHandler(handler2)
logger.propagate = False

NHK_RSS_URL = 'https://www3.nhk.or.jp/rss/news/cat0.xml'
NHK_PREVIOUS_URL_FILE = 'data_files/nhk_previous_url.txt'
NHK_USERNAME = os.getenv("NHK_TRUTHSOCIAL_USERNAME")
NHK_PASSWORD = os.getenv("NHK_TRUTHSOCIAL_PASSWORD")


def publish():
    updated_articles = get_updated_articles(NHK_RSS_URL, NHK_PREVIOUS_URL_FILE)

    if not updated_articles:
        logger.debug("no article")

    for article in updated_articles:
        logger.debug(article.title)
        content = f'{article.title}\n{article.link}\n#nhk_news #inkei_news'
        compose_truth(NHK_USERNAME, NHK_PASSWORD, content)
        time.sleep(5)


if __name__ == '__main__':
    publish()
