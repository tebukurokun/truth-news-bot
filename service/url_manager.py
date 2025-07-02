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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS published_urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT,
                    title TEXT,
                    source TEXT,
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(url, title)
                )
            """
            )

            # インデックス作成
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_published_urls_url ON published_urls(url)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_published_urls_published_at ON published_urls(published_at)"
            )
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
        """新しいURLを登録"""
        try:
            with self.get_connection() as conn:
                if source:
                    conn.execute(
                        """
                        INSERT INTO published_urls (url, title, source) 
                        VALUES (?, ?, ?)
                    """,
                        (url, title, source.value),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO published_urls (url, title) 
                        VALUES (?, ?)
                    """,
                        (url, title),
                    )
                conn.commit()
                logger.debug(f"URL added: {url}")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"URL already exists: {url}")
            return False

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
