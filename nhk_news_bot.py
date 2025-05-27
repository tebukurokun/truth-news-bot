import os
import time
from logging import getLogger, StreamHandler, DEBUG, FileHandler

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

RSS_URL = 'https://www3.nhk.or.jp/rss/news/cat0.xml'
PREVIOUS_URL_FILE = 'data_files/nhk_previous_url.txt'
NHK_USERNAME = os.getenv("NHK_TRUTHSOCIAL_USERNAME")
NHK_PASSWORD = os.getenv("NHK_TRUTHSOCIAL_PASSWORD")
NHK_TOKEN = os.getenv("NHK_TRUTHSOCIAL_TOKEN")


def publish():
    updated_articles = get_updated_articles(RSS_URL, PREVIOUS_URL_FILE)

    if not updated_articles:
        logger.debug("no article(nhk)")
        return

    for article in updated_articles:
        logger.debug(f'nhk: {article.title}')
        content = f'{article.title}\n{article.link}\n#nhk_news #inkei_news'

        try:
            compose_truth(
                NHK_USERNAME, NHK_PASSWORD, NHK_TOKEN, content
            )
            # 成功したら投稿済みurlとして保存.
            save_new_article_url(article.link, PREVIOUS_URL_FILE)

        except Exception as e:
            logger.error(f"Failed to post article: {e}")
            continue
        finally:
            time.sleep(10)


if __name__ == '__main__':
    publish()
