import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional

from models import Media
from utils import setup_logger

logger = setup_logger(__name__)


class URLManager:
    """ニュースボット用URL管理クラス"""

    def __init__(self):

        self.db_path = os.getenv("DATABASE_PATH", "/app/db/newsbot.db")
        self.lock = threading.Lock()
        self.init_db()

    @contextmanager
    def get_connection(self):
        """スレッドセーフなDB接続コンテキストマネージャー"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
            try:
                yield conn
            except Exception as e:
                conn.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                conn.close()

    def init_db(self):
        """データベースとテーブルの初期化"""
        with self.get_connection() as conn:
            # メインテーブル作成
            conn.execute("""
                CREATE TABLE IF NOT EXISTS published_urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT,
                    title TEXT,
                    source TEXT,
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(url, title)
                )
            """)

            # urlとtitleの複合インデックス作成
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_url_title
                ON published_urls (url, title)
            """)
            conn.commit()
            logger.info("Database initialized successfully")

    def is_published(self, url: str, title: str = None) -> bool:
        """URLが既に投稿済みかチェック"""
        with self.get_connection() as conn:
            if title:
                result = conn.execute(
                    "SELECT 1 FROM published_urls WHERE url = ? AND title = ? LIMIT 1",
                    (url, title),
                ).fetchone()
            else:
                result = conn.execute(
                    "SELECT 1 FROM published_urls WHERE url = ? LIMIT 1", (url,)
                ).fetchone()
            return result is not None

    def add_url(
        self,
        url: str,
        title: Optional[str] = None,
        source: Optional[Media] = None,
    ) -> bool:
        """新しいURLを登録。新規登録できたら True、既に登録済みなら False。

        重複は例外ではなく ON CONFLICT DO NOTHING で捌く。同じ記事が複数回
        キューに入るのは正常な動作（DB に入るのはキューから取り出した時点なので、
        投稿間隔の長いレーンでは滞留中に rss_checker が同じ記事を再投入する）で、
        これを IntegrityError にすると get_connection が想定内の重複を
        ERROR ログに出し、ntfy へ通知が飛んでしまう。
        ここを例外にしないことで、NOT NULL 違反など本物の IntegrityError だけが
        main.py のリトライまでバブルアップする。
        """
        with self.get_connection() as conn:
            if source:
                cursor = conn.execute(
                    """
                    INSERT INTO published_urls (url, title, source)
                    VALUES (?, ?, ?)
                    ON CONFLICT DO NOTHING
                """,
                    (url, title, source.value),
                )
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO published_urls (url, title)
                    VALUES (?, ?)
                    ON CONFLICT DO NOTHING
                """,
                    (url, title),
                )
            conn.commit()

            if cursor.rowcount == 0:
                logger.warning(f"URL already exists: {url}")
                return False

            logger.debug(f"URL added: {url}")
            return True

    def cleanup_old_urls(self, days: int = 30) -> int:
        """古いURLデータを削除"""
        cutoff_date = datetime.now() - timedelta(days=days)
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM published_urls 
                WHERE published_at < ?
            """,
                (cutoff_date,),
            )
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Cleaned up {deleted_count} old URLs")
            return deleted_count

    def migration(self):
        """データファイルからURLを登録
        migrationが終わったら削除
        """

        logger.info("Starting migration from data files")
        data_dir = "data_files"
        if not os.path.exists(data_dir):
            logger.error(f"Data directory does not exist: {data_dir}")
            return
        with self.get_connection() as conn:
            for filename in os.listdir(data_dir):
                if filename.endswith(".txt"):
                    file_path = os.path.join(data_dir, filename)
                    print(file_path)
                    with open(file_path, "r", encoding="utf-8") as file:
                        for line in file:
                            url = line.strip()
                            if url:
                                try:
                                    conn.execute(
                                        """
                                        INSERT INTO published_urls (url) 
                                        VALUES (?)
                                    """,
                                        (url,),
                                    )
                                    logger.info(f"URL migrated: {url}")
                                except sqlite3.IntegrityError:
                                    logger.warning(f"URL already exists: {url}")
            conn.commit()

        logger.info("Migration completed successfully")
        return


# 使用例とテスト用のコード
if __name__ == "__main__":
    # 使用例
    url_manager = URLManager()

    # URL登録
    url_manager.add_url("https://example.com/article1", "テスト記事1", "tech_news")

    # 重複チェック
    print(url_manager.is_published("https://example.com/article1"))  # True
    print(url_manager.is_published("https://example.com/article2"))  # False
