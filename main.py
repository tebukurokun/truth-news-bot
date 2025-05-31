import os
import queue
import threading
import time
from logging import getLogger, StreamHandler, DEBUG, FileHandler, Formatter

from news_bot_v2 import check_update, publish

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)

formatter = Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

if os.path.exists("/proc/1/fd/1"):
    handler2 = FileHandler("/proc/1/fd/1")
    handler2.setFormatter(formatter)
    logger.addHandler(handler2)

logger.setLevel(DEBUG)
logger.propagate = False


# queue.Queue()を使用して、記事をキューに入れる
article_queue = queue.Queue()

# 最大リトライ回数
MAX_RETRY = 20


def rss_checker():
    while True:
        articles = check_update()

        if articles:
            for article in articles:
                article_queue.put((article, 0))

        time.sleep(60)


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
                    logger.error(f"Max retry exceeded: {article.title}")

                article_queue.task_done()

        except queue.Empty:
            pass

        time.sleep(10)


if __name__ == "__main__":
    threading.Thread(target=rss_checker, daemon=True).start()
    threading.Thread(target=sns_publisher, daemon=True).start()

    while True:
        time.sleep(1)  # メインスレッドは生存だけさせる
