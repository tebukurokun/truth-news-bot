import os
import queue
import socket
import threading
import time
from datetime import timedelta
from typing import Optional

from dotenv import load_dotenv

from models import Media
from news_bot import SLOW_MEDIA_MAX_AGE, check_update, is_stale, publish
from service.url_manager import URLManager
from utils import setup_logger

logger = setup_logger(__name__)
load_dotenv()  # take environment variables from .env.

# feedparser は timeout 引数を持たず、既定のソケットタイムアウト（無制限）に従う。
# 応答しないフィードサーバで rss_checker が無期限ブロックするのを防ぐ。
# curl_cffi は libcurl を使うため、Truth Social への投稿側には影響しない。
socket.setdefaulttimeout(30)


# 投稿間隔（秒）。Truth Social のレート制限回避のため、安易に縮めない。
POST_INTERVAL_SECONDS = int(os.getenv("POST_INTERVAL_SECONDS", 11))
SLOW_POST_INTERVAL_SECONDS = int(os.getenv("SLOW_POST_INTERVAL_SECONDS", 600))

# queue.Queue()を使用して、記事をキューに入れる。
# 投稿間隔がメディアごとに違うので、キューと publisher スレッドをレーンに分ける
# （同じキューで 10 分待たせると、他メディアの投稿まで止まってしまう）。
article_queue = queue.Queue()
slow_queues = {
    Media.ASAHI_SANKEI: queue.Queue(),
    Media.NIKKEI: queue.Queue(),
}

# 最大リトライ回数
MAX_RETRY = int(os.getenv("MAX_RETRY", 10))

# URLManager初期化
url_manager = URLManager()


def rss_checker():
    while True:
        try:
            articles = check_update(url_manager.is_published)

            if articles:
                for article in articles:
                    slow_queues.get(article.media, article_queue).put((article, 0))

        except Exception:
            # ここで握らないとスレッドが死に、プロセスは生きたまま
            # ニュース取得だけが停止する（restart も healthcheck も検知できない）。
            logger.exception("RSS check failed")

        time.sleep(300)


def sns_publisher(
    post_queue: queue.Queue,
    interval: int,
    max_age: Optional[timedelta] = None,
):
    """
    キューから記事を1件取り出して投稿し、interval 秒あけて次に進む。

    スリープするのは実際に投稿を試みたときだけ。古い記事の破棄や重複スキップで
    interval を消費すると、投稿間隔の長いレーンではそのぶん投稿が止まってしまう。
    """
    while True:
        try:
            article, retry_count = post_queue.get(timeout=10)

        except queue.Empty:
            continue

        # キューに滞留している間に古くなった記事は投稿しない。
        # check_update() 側でも取得時に同じ判定をしているが、投稿間隔の長いレーンでは
        # 投入から投稿まで数十分〜数時間あくため、ここでも見る必要がある。
        if is_stale(article, max_age):
            logger.info(f"Dropped stale article: {article.title} - {article.link}")
            post_queue.task_done()
            continue

        try:
            posted = publish(article, url_manager.is_published, url_manager.add_url)
            post_queue.task_done()

            if not posted:
                # 重複・連載スキップで投稿していないので、間隔をあけずに次へ
                continue

        except Exception as e:
            logger.warning(
                f"Publish failed: {article.title}, retry: {retry_count}, error: {e}"
            )

            if retry_count < MAX_RETRY:
                post_queue.put((article, retry_count + 1))
            else:
                logger.error(f"Max retry exceeded: {article.title} - {article.link}")

            post_queue.task_done()

        time.sleep(interval)


if __name__ == "__main__":
    logger.info("main started")
    threading.Thread(target=rss_checker, daemon=True).start()
    threading.Thread(
        target=sns_publisher,
        args=(article_queue, POST_INTERVAL_SECONDS),
        daemon=True,
    ).start()

    # 朝日・産経 / 日経はメディアごとに 1 スレッド。互いに待たせないため。
    for media, media_queue in slow_queues.items():
        threading.Thread(
            target=sns_publisher,
            args=(media_queue, SLOW_POST_INTERVAL_SECONDS, SLOW_MEDIA_MAX_AGE),
            name=f"sns_publisher_{media.value}",
            daemon=True,
        ).start()

    while True:
        time.sleep(1)  # メインスレッドは生存だけさせる
