import os
import queue
import threading
import time

from dotenv import load_dotenv

from news_bot import check_update, publish
from service.url_manager import URLManager
from utils import setup_logger

logger = setup_logger(__name__)
load_dotenv()  # take environment variables from .env.


# queue.Queue()を使用して、記事をキューに入れる
article_queue = queue.Queue()

# 最大リトライ回数
MAX_RETRY = int(os.getenv("MAX_RETRY", 10))

# URLManager初期化
url_manager = URLManager()


def rss_checker():
    while True:
        articles = check_update(url_manager.is_published)

        if articles:
            for article in articles:
                article_queue.put((article, 0))

        time.sleep(300)


def sns_publisher():
    while True:
        try:
            article, retry_count = article_queue.get(timeout=10)
            try:
                publish(article, url_manager.is_published, url_manager.add_url)
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
