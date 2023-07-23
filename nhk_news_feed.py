from typing import List, Set

import feedparser
import pytz
from dataclasses import dataclass

RSS_URL = 'https://www3.nhk.or.jp/rss/news/cat0.xml'
JST = pytz.timezone('Asia/Tokyo')
PREVIOUS_URL_FILE = 'data_files/nhk_previous_url.txt'


@dataclass
class Article:
    title: str
    link: str


def _get_previous_article_urls() -> Set[str]:
    """
    前回の処理で存在した記事のurlをsetで取得.
    """
    with open(PREVIOUS_URL_FILE) as f:
        urls = set(s.strip() for s in f.readlines())
    return urls


def _save_article_urls(urls: list[str]):
    with open(PREVIOUS_URL_FILE, 'w', encoding = "utf-8") as txt_file:
        txt_file.write("\n".join(urls))


def get_updated_articles() -> List[Article]:
    """
    更新された記事を取得.
    """
    # rssのurlから記事取得
    rss_data = feedparser.parse(RSS_URL)
    rss_entries = rss_data.entries

    # 前回の記事のurlを取得
    previous_urls = _get_previous_article_urls()
    # 今回の記事のurlを保存
    _save_article_urls([entry.link for entry in  rss_entries])

    updated_entries = []

    for entry in rss_entries:
        # e.g. {'title': '川で溺れ女子児童3人死亡 花を手向ける人たちの姿 福岡 宮若', 'title_detail': {'type': 'text/plain', 'language': None, 'base': 'https://www3.nhk.or.jp/rss/news/cat0.xml', 'value': '川で溺れ女子児童3人死亡 花を手向ける人たちの姿 福岡 宮若'}, 'links': [{'rel': 'alternate', 'type': 'text/html', 'href': 'http://www3.nhk.or.jp/news/html/20230722/k10014138851000.html'}], 'link': 'http://www3.nhk.or.jp/news/html/20230722/k10014138851000.html', 'id': 'http://www3.nhk.or.jp/news/html/20230722/k10014138851000.html', 'guidislink': False, 'published': 'Sat, 22 Jul 2023 11:56:39 +0900', 'published_parsed': time.struct_time(tm_year=2023, tm_mon=7, tm_mday=22, tm_hour=2, tm_min=56, tm_sec=39, tm_wday=5, tm_yday=203, tm_isdst=0), 'summary': '21日、福岡県宮若市で川遊びをしていた小学6年生の女子児童3人が溺れて死亡した川には、22日朝、花を手向ける人たちの姿が見られ、夏休み初日に失われた幼い命を惜しむ声が聞かれました。', 'summary_detail': {'type': 'text/html', 'language': None, 'base': 'https://www3.nhk.or.jp/rss/news/cat0.xml', 'value': '21日、福岡県宮若市で川遊びをしていた小学6年生の女子児童3人が溺れて死亡した川には、22日朝、花を手向ける人たちの姿が見られ、夏休み初日に失われた幼い命を惜しむ声が聞かれました。'}, 'nhknews_new': 'false'}

        # 前回チェック時から追加されたurlを処理対象とする
        if entry.link not in previous_urls:
            updated_entries.append(Article(entry.title, entry.link))

    return updated_entries


if __name__ == '__main__':
    print(get_updated_articles())
