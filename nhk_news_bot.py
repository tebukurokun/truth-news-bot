import time
import os
from news_feeder import get_updated_articles, save_new_article_urls
from truth_social import compose_truth
from logging import getLogger, StreamHandler, DEBUG, FileHandler

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler2 = FileHandler(filename="/proc/1/fd/1")
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.addHandler(handler2)
logger.propagate = False

NHK_RSS_URL = 'https://www3.nhk.or.jp/rss/news/cat0.xml'
NHK_PREVIOUS_URL_FILE = 'data_files/nhk_previous_url.txt'
NHK_USERNAME = os.getenv("NHK_TRUTHSOCIAL_USERNAME")
NHK_PASSWORD = os.getenv("NHK_TRUTHSOCIAL_PASSWORD")
NHK_TOKEN = os.getenv("NHK_TRUTHSOCIAL_TOKEN")


def publish():
    updated_articles = get_updated_articles(NHK_RSS_URL, NHK_PREVIOUS_URL_FILE)

    if not updated_articles:
        logger.debug("no article(nhk)")
        return

    for article in updated_articles:
        logger.debug(f'nhk: {article.title}')
        content = f'{article.title}\n{article.link}\n#nhk_news #inkei_news'
        compose_truth(NHK_USERNAME, NHK_PASSWORD, NHK_TOKEN, content)
        time.sleep(10)

    # 成功したら投稿済みurlとして保存.
    save_new_article_urls(
        [article.link for article in updated_articles], NHK_PREVIOUS_URL_FILE
    )


if __name__ == '__main__':
    publish()
