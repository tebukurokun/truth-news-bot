import queue
import threading
import time

from news_bot_v2 import check_update, publish
from utils import setup_logger

logger = setup_logger(__name__)


# queue.Queue()を使用して、記事をキューに入れる
article_queue = queue.Queue()

# 最大リトライ回数
MAX_RETRY = 10


def rss_checker():
    while True:
        articles = check_update()

        if articles:
            for article in articles:
                article_queue.put((article, 0))

        time.sleep(300)


def sns_publisher():
    while True:
        try:
            article, retry_count = article_queue.get(timeout=10)
            try:
                publish(article)
                article_queue.task_done()

            except Exception as e:
                logger.warning(
                    f"Publish failed: {article.title}, retry: {retry_count}, error: {e}"
                )

                if retry_count < MAX_RETRY:
                    article_queue.put((article, retry_count + 1))
                else:
                    logger.error(
                        f"Max retry exceeded: {article.title} - {article.link}"
                    )

                article_queue.task_done()

        except queue.Empty:
            pass

        time.sleep(11)


if __name__ == "__main__":
    threading.Thread(target=rss_checker, daemon=True).start()
    threading.Thread(target=sns_publisher, daemon=True).start()

    while True:
        time.sleep(1)  # メインスレッドは生存だけさせる
