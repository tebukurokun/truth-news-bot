from nhk_news_feed import get_updated_articles
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


def publish():
    updated_articles = get_updated_articles()

    if not updated_articles:
        logger.debug("no article")

    for article in updated_articles:
        logger.debug(article.title)
        content = f'{article.title}\n{article.link}\n#nhk_news #inkei_news'
        compose_truth(content)


if __name__ == '__main__':
    publish()
