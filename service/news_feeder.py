from typing import List, Set

import feedparser

from models import Article


def get_past_article_urls(previous_url_file: str) -> Set[str]:
    """
    前回の処理で存在した記事のurlをsetで取得.
    """
    with open(previous_url_file) as f:
        urls = set(s.strip() for s in f.readlines())
    return urls


def save_new_article_urls(mew_urls: list[str], previous_url_file: str):
    with open(previous_url_file, "a", encoding="utf-8") as txt_file:
        txt_file.write("\n".join(mew_urls) + "\n")


def save_new_article_url(new_url: str, previous_url_file: str):
    with open(previous_url_file, "a", encoding="utf-8") as txt_file:
        txt_file.write(new_url + "\n")


def get_updated_articles(url: str, previous_url_file: str) -> List[Article]:
    """
    更新された記事を取得.
    """
    # rssのurlから記事取得
    rss_data = feedparser.parse(url)
    rss_entries = rss_data.entries

    # 前回の記事のurlを取得
    past_urls = get_past_article_urls(previous_url_file)

    updated_entries = []

    for entry in rss_entries:
        # e.g. {'title': '川で溺れ女子児童3人死亡 花を手向ける人たちの姿 福岡 宮若', 'title_detail': {'type': 'text/plain', 'language': None, 'base': 'https://www3.nhk.or.jp/rss/news/cat0.xml', 'value': '川で溺れ女子児童3人死亡 花を手向ける人たちの姿 福岡 宮若'}, 'links': [{'rel': 'alternate', 'type': 'text/html', 'href': 'http://www3.nhk.or.jp/news/html/20230722/k10014138851000.html'}], 'link': 'http://www3.nhk.or.jp/news/html/20230722/k10014138851000.html', 'id': 'http://www3.nhk.or.jp/news/html/20230722/k10014138851000.html', 'guidislink': False, 'published': 'Sat, 22 Jul 2023 11:56:39 +0900', 'published_parsed': time.struct_time(tm_year=2023, tm_mon=7, tm_mday=22, tm_hour=2, tm_min=56, tm_sec=39, tm_wday=5, tm_yday=203, tm_isdst=0), 'summary': '21日、福岡県宮若市で川遊びをしていた小学6年生の女子児童3人が溺れて死亡した川には、22日朝、花を手向ける人たちの姿が見られ、夏休み初日に失われた幼い命を惜しむ声が聞かれました。', 'summary_detail': {'type': 'text/html', 'language': None, 'base': 'https://www3.nhk.or.jp/rss/news/cat0.xml', 'value': '21日、福岡県宮若市で川遊びをしていた小学6年生の女子児童3人が溺れて死亡した川には、22日朝、花を手向ける人たちの姿が見られ、夏休み初日に失われた幼い命を惜しむ声が聞かれました。'}, 'nhknews_new': 'false'}

        # 前回チェック時から追加されたurlを処理対象とする
        if entry.link not in past_urls:
            updated_entries.append(Article(entry.title, entry.link))

    return updated_entries
