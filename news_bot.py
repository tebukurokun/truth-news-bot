import os
import random
from datetime import datetime, timedelta, timezone
from typing import List, Callable, Optional

from dotenv import load_dotenv

from models import Media, Article
from service.news_feeder import get_articles
from service.truth_social import compose_truth
from utils import setup_logger

logger = setup_logger(__name__)


load_dotenv()  # take environment variables from .env.

NHK_RSS_URL = "https://news.web.nhk/n-data/conf/na/rss/cat0.xml"
NHK_USERNAME = os.getenv("NHK_TRUTHSOCIAL_USERNAME")
NHK_PASSWORD = os.getenv("NHK_TRUTHSOCIAL_PASSWORD")
NHK_TOKEN = os.getenv("NHK_TRUTHSOCIAL_TOKEN")

ASAHI_RSS_URL = "https://www.asahi.com/rss/asahi/newsheadlines.rdf"
SANKEI_RSS_URL = "https://assets.wor.jp/rss/rdf/sankei/flash.rdf"
ASAHI_SANKEI_USERNAME = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_USERNAME")
ASAHI_SANKEI_PASSWORD = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_PASSWORD")
ASAHI_SANKEI_TOKEN = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_TOKEN")

BBC_WEB_RSS_URL = "http://feeds.bbci.co.uk/japanese/rss.xml"
BBC_YOUTUBE_RSS_URL = (
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCCcey5CP5GDZeom987gqTdg"
)
BBC_USERNAME = os.getenv("BBC_TRUTHSOCIAL_USERNAME")
BBC_PASSWORD = os.getenv("BBC_TRUTHSOCIAL_PASSWORD")
BBC_TOKEN = os.getenv("BBC_TRUTHSOCIAL_TOKEN")

CNN_RSS_URL = "http://feeds.cnn.co.jp/rss/cnn/cnn.rdf"
CNN_USERNAME = os.getenv("CNN_TRUTHSOCIAL_USERNAME")
CNN_PASSWORD = os.getenv("CNN_TRUTHSOCIAL_PASSWORD")
CNN_TOKEN = os.getenv("CNN_TRUTHSOCIAL_TOKEN")

NIKKEI_RSS_URL = "https://assets.wor.jp/rss/rdf/nikkei/news.rdf"
NIKKEI_USERNAME = os.getenv("NIKKEI_TRUTHSOCIAL_USERNAME")
NIKKEI_PASSWORD = os.getenv("NIKKEI_TRUTHSOCIAL_PASSWORD")
NIKKEI_TOKEN = os.getenv("NIKKEI_TRUTHSOCIAL_TOKEN")

# 投稿間隔の長いメディア（朝日・産経 / 日経）は、記事の生成が投稿を上回るため
# 配信から一定時間より古い記事は投稿せずに捨てる。main.py 側でも
# キューから取り出した時点で同じ判定をする（滞留中に古くなるため）。
SLOW_MEDIA_MAX_AGE = timedelta(hours=int(os.getenv("SLOW_MEDIA_MAX_AGE_HOURS", 5)))


def is_stale(article: Article, max_age: Optional[timedelta]) -> bool:
    """配信日時が max_age より古いか。日時が取れていない記事は古くない扱い。"""
    if max_age is None or article.published_at is None:
        return False

    return datetime.now(timezone.utc) - article.published_at > max_age


def check_update(is_published: Callable[[str, Optional[str]], bool]) -> List[Article]:
    nhk_articles = _process_articles(
        NHK_RSS_URL, Media.NHK, is_published, max_articles=2
    )

    asahi_sankei_articles = _process_articles(
        ASAHI_RSS_URL,
        Media.ASAHI_SANKEI,
        is_published,
        max_articles=1,
        max_age=SLOW_MEDIA_MAX_AGE,
    ) + _process_articles(
        SANKEI_RSS_URL,
        Media.ASAHI_SANKEI,
        is_published,
        max_articles=1,
        max_age=SLOW_MEDIA_MAX_AGE,
    )

    bbc_articles = _process_articles(
        BBC_WEB_RSS_URL, Media.BBC, is_published, max_articles=1
    ) + _process_articles(BBC_YOUTUBE_RSS_URL, Media.BBC, is_published, max_articles=1)

    cnn_articles = _process_articles(
        CNN_RSS_URL, Media.CNN, is_published, max_articles=1
    )

    nikkei_articles = _process_articles(
        NIKKEI_RSS_URL,
        Media.NIKKEI,
        is_published,
        max_articles=1,
        max_age=SLOW_MEDIA_MAX_AGE,
    )

    if (
        not nhk_articles
        and not asahi_sankei_articles
        and not bbc_articles
        and not cnn_articles
        and not nikkei_articles
    ):
        logger.debug("no article")
        return []

    return (
        nhk_articles
        + asahi_sankei_articles
        + bbc_articles
        + cnn_articles
        + nikkei_articles
    )


def publish(
    article: Article,
    is_published: Callable[[str, Optional[str]], bool],
    add_url: Callable[[str, Optional[str], Optional[Media]], bool],
) -> bool:
    """
    記事を投稿する。実際に投稿したら True、投稿せずスキップしたら False を返す。

    呼び出し側（main.py）は True のときだけ投稿間隔をスリープする。
    重複や連載スキップで 10 分待つと、そのぶん投稿が止まってしまうため。
    """
    match article.media:
        case Media.NHK:
            content = f"{article.title}\n{article.link}\n#nhk_news #inkei_news"

            return _post_and_save(
                article,
                content,
                article.media,
                is_published,
                add_url,
                NHK_USERNAME,
                NHK_PASSWORD,
                NHK_TOKEN,
            )

        case Media.ASAHI_SANKEI:
            tag = (
                "#asahi_news #inkei_news"
                if "asahi.com" in article.link
                else "#sankei_news #inkei_news"
            )

            if article.title.startswith("【") or article.title.startswith("＜"):
                # "【" or "＜"のときはスキップし投稿済みurlとして保存.
                add_url(article.link, article.title, article.media)
                return False

            content = f"{article.title}\n{article.link}\n{tag}"

            return _post_and_save(
                article,
                content,
                article.media,
                is_published,
                add_url,
                ASAHI_SANKEI_USERNAME,
                ASAHI_SANKEI_PASSWORD,
                ASAHI_SANKEI_TOKEN,
            )

        case Media.BBC:
            content = f"{article.title}\n{article.link}\n#bbc_news #inkei_news"
            return _post_and_save(
                article,
                content,
                article.media,
                is_published,
                add_url,
                BBC_USERNAME,
                BBC_PASSWORD,
                BBC_TOKEN,
            )

        case Media.CNN:
            content = f"{article.title}\n{article.link}\n#cnn_news #inkei_news"

            return _post_and_save(
                article,
                content,
                article.media,
                is_published,
                add_url,
                CNN_USERNAME,
                CNN_PASSWORD,
                CNN_TOKEN,
            )

        case Media.NIKKEI:
            content = f"{article.title}\n{article.link}\n #nikkei_news #inkei_news"

            return _post_and_save(
                article,
                content,
                article.media,
                is_published,
                add_url,
                NIKKEI_USERNAME,
                NIKKEI_PASSWORD,
                NIKKEI_TOKEN,
            )

        case _:
            logger.warning(f"Unknown media: {article.media} - {article.link}")
            return False


def _process_articles(
    rss_url: str,
    media: Media,
    is_published: Callable[[str, Optional[str]], bool],
    max_articles: int = 2,
    max_age: Optional[timedelta] = None,
) -> List[Article]:
    """記事を取得し、未公開記事からランダムに選択してメディア情報を設定"""
    articles = get_articles(rss_url)

    # 未公開記事のみをフィルタリング
    unpublished_articles = [
        article for article in articles if not is_published(article.link, None)
    ]

    # 古い記事は母集団から外す。投稿間隔の長いメディアでは、これをやらないと
    # 抽選の母集団が古い記事で埋まり、キューも古い記事ばかりになる。
    if max_age is not None:
        fresh_articles = [
            article
            for article in unpublished_articles
            if not is_stale(article, max_age)
        ]
        stale_count = len(unpublished_articles) - len(fresh_articles)
        if stale_count:
            logger.debug(f"Skipped {stale_count} stale entries - {rss_url}")
        unpublished_articles = fresh_articles

    # ランダムに指定数を選択
    selected_articles = random.sample(
        unpublished_articles, min(max_articles, len(unpublished_articles))
    )

    # メディア情報を設定
    for article in selected_articles:
        article.media = media

    return selected_articles


def _post_and_save(
    article: Article,
    content: str,
    media: Media,
    is_published: Callable[[str, Optional[str]], bool],
    add_url: Callable[[str, Optional[str], Optional[Media]], bool],
    user_name: str,
    password: str,
    token: str,
) -> bool:
    """
    指定された記事を投稿し、投稿済みのURLを保存する関数.
    投稿したら True、既に投稿済みでスキップしたら False を返す.
    :param article: 投稿する記事
    :param content: 投稿する内容
    :param media: 記事のメディア情報
    :param is_published: URLが既に投稿済みかどうかを確認する関数
    :param add_url: 投稿済みのURLを保存する関数
    :param user_name: Truth Socialのユーザー名
    :param password: Truth Socialのパスワード
    :param token: Truth Socialのトークン
    """
    try:
        if is_published(article.link, None):
            # 既に投稿済みのURLの場合はスキップ
            return False
        compose_truth(user_name, password, token, content)
        add_url(article.link, article.title, media)
        logger.info(f"Published: {article.title} - {article.link}")
        return True

    except Exception as e:
        raise e
