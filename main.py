import asyncio
from asyncio.tasks import gather
import time
import sys

import requests
from bs4 import BeautifulSoup

async def async_get_page(keyword=None, type="like", page=1):
    """
    URLを生成し、ページを取得(async)

    Parameters
    ----------
    keyword : str or None, default None
        検索キーワード
    type : str, default "like"
        記事のソートの種類
    page : int, default 1
        記事のページ番号

    Returns
    -------
    str
        URLから取得したページのhtmlの文字列
    """
    keyword = "+".join(keyword.split(" "))
    if keyword is not None:
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, requests.get, f"https://qiita.com/search?page={page}&q={keyword}&sort={type}")
        return resp.text

def get_soup(str_html):
    """
    htmlをhtml.parserでパース

    Parameters
    ----------
    str_html : str
        取得したhtmlの文字列

    Returns
    -------
    object
        html.parserでパースされたhtmlのBeautifulSoupオブジェクト
    """
    return BeautifulSoup(str_html, "html.parser")

def make_url(path):
    """
    pathからQiitaのURLを作成
    """
    return f"https://qiita.com{path}"

def search_articles(parsed_html) -> list:
    """
    すべての記事のdiv要素を抽出して、リストを返す

    Parameters
    ----------
    parsed_html : object
        パースしたhtmlのBeautifulSoupオブジェクト

    Returns
    -------
    list
        すべての記事のdiv要素をまとめたリスト

    See Also
    --------
    get_soup : 文字列のhtmlからパースされたBeautifulSoupオブジェクトを取得
    """
    return [i for i in parsed_html.find_all("div", class_="searchResult")]

def search_article_title(parsed_article_html):
    """
    記事のdiv要素内から、記事のタイトルを抽出

    Parameters
    ----------
    parsed_article_html : object
        パースされたhtmlのBeautifulSoupオブジェクト

    Returns
    -------
    str
        記事のURLの文字列(make_urlを使って、パスをURLに変換)
    str
        記事のタイトルの文字列
    """
    title = parsed_article_html.find("h1", class_="searchResult_itemTitle")
    title_link = title.find("a")
    return make_url(title_link["href"]), title_link.text

def search_article_tags(parsed_article_html) -> list:
    """
    記事のdiv要素内から、記事のタグを抽出

    Parameters
    ----------
    parsed_article_html : object
        パースされたhtmlのBeautifulSoupオブジェクト

    Returns
    -------
    list
        記事のタグのリスト（1以上）
    """
    tags = parsed_article_html.find("ul", class_="list-unstyled list-inline tagList")
    return [i.text for i in tags.select("li > a")]

def search_article_text(parsed_article_html) -> str:
    """
    記事のdiv要素内から、記事の本文を抽出

    Parameters
    ----------
    parsed_article_html : object
        パースされたhtmlのBeautifulSoupオブジェクト

    Returns
    -------
    str
        記事の本文(一部).改行による文字列の乱れを修正済
    """
    contents = parsed_article_html.find("div", class_="searchResult_snippet")
    return contents.text.replace("\n", "")

def async_get_all_contents(keyword, limit=1):
    """
    検索結果のページを探索して、検索結果のページが複数にわたる場合には
    非同期でリクエストを送り、取得したデータのリストを返す

    Parameters
    ----------
    keyword : str
        検索キーワード
    limit : int
        探索するページ数の上限

    Returns
    -------
    list
        各ページのパースされたhtmlのBeautifulSoupオブジェクトのリスト
    """
    loop = asyncio.get_event_loop()
    async def limited_get_contents(keyword, page):
        async with asyncio.Semaphore(5):
            return await async_get_page(keyword, page=page)
    tasks = [limited_get_contents(keyword, page=i) for i in range(1, limit+1)]
    results = loop.run_until_complete(asyncio.gather(*tasks))
    all_list = []
    for result in results:
        l = search_articles(get_soup(result))
        all_list.extend(l)
    return all_list

def make_article_dict(parsed_article_html) -> dict:
    """
    記事から抽出したデータから辞書を作成

    Parameters
    ----------
    parsed_article_html : object
        パースしたhtmlのBeautifulSoupオブジェクト

    Returns
    -------
    dict
        記事のデータの辞書(タイトル(title)、URL(url)、タグ(tags)、本文(text))
    """
    contents_data = {}
    url, title = search_article_title(parsed_article_html)
    contents_data["title"] = title
    contents_data["url"] = url
    contents_data["tags"] = ", ".join(search_article_tags(parsed_article_html))
    contents_data["text"] = search_article_text(parsed_article_html)
    return contents_data

def main():
    keyword = sys.argv[1]
    limit = sys.argv[2]

    for i, content in enumerate(async_get_all_contents(keyword=keyword, limit=int(limit))):
        print(f"Contents: {i+1}")
        data = make_article_dict(content)
        print(f"Dictionary Data -> {data}\n")

if __name__ == "__main__":
    start = time.time()
    main()
    elapsed_time = time.time() - start
    print(f"main(): {elapsed_time}s\n")