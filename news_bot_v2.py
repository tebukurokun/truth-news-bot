import os
import random
from typing import List

from dotenv import load_dotenv

from models import Media, Article
from service.news_feeder import (
    get_updated_articles,
    save_new_article_url,
    get_past_article_urls,
)
from service.truth_social import compose_truth
from utils import setup_logger

logger = setup_logger(__name__)


load_dotenv()  # take environment variables from .env.

NHK_RSS_URL = "https://www3.nhk.or.jp/rss/news/cat0.xml"
NHK_PREVIOUS_URL_FILE = "data_files/nhk_previous_url.txt"
NHK_USERNAME = os.getenv("NHK_TRUTHSOCIAL_USERNAME")
NHK_PASSWORD = os.getenv("NHK_TRUTHSOCIAL_PASSWORD")
NHK_TOKEN = os.getenv("NHK_TRUTHSOCIAL_TOKEN")

ASAHI_RSS_URL = "https://www.asahi.com/rss/asahi/newsheadlines.rdf"
ASAHI_PREVIOUS_URL_FILE = "data_files/asahi_previous_url.txt"
SANKEI_RSS_URL = "https://assets.wor.jp/rss/rdf/sankei/flash.rdf"
SANKEI_PREVIOUS_URL_FILE = "data_files/sankei_previous_url.txt"
ASAHI_SANKEI_USERNAME = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_USERNAME")
ASAHI_SANKEI_PASSWORD = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_PASSWORD")
ASAHI_SANKEI_TOKEN = os.getenv("ASAHI_SANKEI_TRUTHSOCIAL_TOKEN")

BBC_WEB_RSS_URL = "http://feeds.bbci.co.uk/japanese/rss.xml"
BBC_WEB_PREVIOUS_URL_FILE = "data_files/bbc_web_previous_url.txt"
BBC_YOUTUBE_RSS_URL = (
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCCcey5CP5GDZeom987gqTdg"
)
BBC_YOUTUBE_PREVIOUS_URL_FILE = "data_files/bbc_youtube_previous_url.txt"
BBC_USERNAME = os.getenv("BBC_TRUTHSOCIAL_USERNAME")
BBC_PASSWORD = os.getenv("BBC_TRUTHSOCIAL_PASSWORD")
BBC_TOKEN = os.getenv("BBC_TRUTHSOCIAL_TOKEN")

CNN_RSS_URL = "http://feeds.cnn.co.jp/rss/cnn/cnn.rdf"
CNN_PREVIOUS_URL_FILE = "data_files/cnn_previous_url.txt"
CNN_USERNAME = os.getenv("CNN_TRUTHSOCIAL_USERNAME")
CNN_PASSWORD = os.getenv("CNN_TRUTHSOCIAL_PASSWORD")
CNN_TOKEN = os.getenv("CNN_TRUTHSOCIAL_TOKEN")


def check_update() -> List[Article]:
    nhk_articles = get_updated_articles(NHK_RSS_URL, NHK_PREVIOUS_URL_FILE)
    nhk_articles = [
        (
            setattr(article, "media", Media.NHK)
            or article  # mediaを設定してArticleを返す
        )
        for article in random.sample(nhk_articles, min(2, len(nhk_articles)))
    ]

    asahi_sankei_articles = get_updated_articles(
        ASAHI_RSS_URL, ASAHI_PREVIOUS_URL_FILE
    ) + get_updated_articles(SANKEI_RSS_URL, SANKEI_PREVIOUS_URL_FILE)
    asahi_sankei_articles = [
        (setattr(article, "media", Media.ASAHI_SANKEI) or article)
        for article in random.sample(
            asahi_sankei_articles, min(2, len(asahi_sankei_articles))
        )
    ]

    bbc_articles = get_updated_articles(
        BBC_WEB_RSS_URL, BBC_WEB_PREVIOUS_URL_FILE
    ) + get_updated_articles(BBC_YOUTUBE_RSS_URL, BBC_YOUTUBE_PREVIOUS_URL_FILE)
    bbc_articles = [
        (setattr(article, "media", Media.BBC) or article)
        for article in random.sample(bbc_articles, min(1, len(bbc_articles)))
    ]

    cnn_articles = get_updated_articles(CNN_RSS_URL, CNN_PREVIOUS_URL_FILE)
    cnn_articles = [
        (setattr(article, "media", Media.CNN) or article)
        for article in random.sample(cnn_articles, min(1, len(cnn_articles)))
    ]

    if (
        not nhk_articles
        and not asahi_sankei_articles
        and not bbc_articles
        and not cnn_articles
    ):
        logger.debug("no article")
        return []

    return nhk_articles + asahi_sankei_articles + bbc_articles + cnn_articles


def publish(article: Article):
    match article.media:
        case Media.NHK:
            content = f"{article.title}\n{article.link}\n#nhk_news #inkei_news"

            _post_and_save(
                article,
                content,
                NHK_PREVIOUS_URL_FILE,
                NHK_USERNAME,
                NHK_PASSWORD,
                NHK_TOKEN,
            )

        case Media.ASAHI_SANKEI:

            previous_url_file = (
                ASAHI_PREVIOUS_URL_FILE
                if "asahi.com" in article.link
                else SANKEI_PREVIOUS_URL_FILE
            )

            tag = (
                "#asahi_news #inkei_news"
                if "asahi.com" in article.link
                else "#sankei_news #inkei_news"
            )

            if article.title.startswith("【") or article.title.startswith("＜"):
                # "【" or "＜"のときはスキップし投稿済みurlとして保存.
                save_new_article_url(article.link, previous_url_file)
                return

            content = f"{article.title}\n{article.link}\n{tag}"

            _post_and_save(
                article,
                content,
                previous_url_file,
                ASAHI_SANKEI_USERNAME,
                ASAHI_SANKEI_PASSWORD,
                ASAHI_SANKEI_TOKEN,
            )

        case Media.BBC:
            previous_url_file = (
                BBC_YOUTUBE_PREVIOUS_URL_FILE
                if "youtube" in article.link
                else BBC_WEB_PREVIOUS_URL_FILE
            )

            content = f"{article.title}\n{article.link}\n#inkei_news #bbc_news"

            _post_and_save(
                article,
                content,
                previous_url_file,
                BBC_USERNAME,
                BBC_PASSWORD,
                BBC_TOKEN,
            )

        case Media.CNN:

            content = f"{article.title}\n{article.link}\n#inkei_news #cnn_news"

            _post_and_save(
                article,
                content,
                CNN_PREVIOUS_URL_FILE,
                CNN_USERNAME,
                CNN_PASSWORD,
                CNN_TOKEN,
            )


def _post_and_save(
    article: Article,
    content: str,
    previous_url_file: str,
    user_name: str,
    password: str,
    token: str,
):
    """
    指定された記事を投稿し、投稿済みのURLを保存する関数.
    :param article: 投稿する記事
    :param previous_url_file: 投稿済みURLを保存するファイルのパス
    :param user_name: Truth Socialのユーザー名
    :param password: Truth Socialのパスワード
    :param token: Truth Socialのトークン
    """
    try:
        if article.link in get_past_article_urls(previous_url_file):
            # 既に投稿済みのURLの場合はスキップ
            return
        compose_truth(user_name, password, token, content)
        save_new_article_url(article.link, previous_url_file)
        logger.info(f"Published article: {article.title} - {article.link}")

    except Exception as e:
        raise e
