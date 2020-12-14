import asyncio
from asyncio.tasks import gather
import time
import sys

import requests
from bs4 import BeautifulSoup

async def async_get_page(keyword="", type="like", page=1):
    keyword = "+".join(keyword.split(" "))
    if keyword != "":
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, requests.get, f"https://qiita.com/search?page={page}&q={keyword}&sort={type}")
        return resp.text

def get_page(keyword="", type="like", page=1): 
    keyword = "+".join(keyword.split(" "))
    try:
        if keyword != "":
            res = requests.get(f"https://qiita.com/search?page={page}&q={keyword}&sort={type}")
            return res.text

    except Exception as e:
        print(e)

def get_soup(html):
    return BeautifulSoup(html, "html.parser")

def make_url(path):
    return f"https://qiita.com{path}"

def search_result(soup) -> list:
    return [i for i in soup.find_all("div", class_="searchResult")]

def search_contents_title(soup):
    title = soup.find("h1", class_="searchResult_itemTitle")
    title_link = title.find("a")
    return make_url(title_link["href"]), title_link.text

def search_tags(soup) -> list:
    tags = soup.find("ul", class_="list-unstyled list-inline tagList")
    return [i.text for i in tags.select("li > a")]

def search_contents_text(soup) -> str:
    contents = soup.find("div", class_="searchResult_snippet")
    return contents.text.replace("\n", "")

def async_get_all_contents(keyword, limit=1):
    loop = asyncio.get_event_loop()
    tasks = [async_get_page(keyword, page=i) for i in range(1, limit+1)]
    results = loop.run_until_complete(asyncio.gather(*tasks))
    all_list = []
    for result in results:
        l = search_result(get_soup(result))
        all_list.extend(l)
    return all_list

def get_all_contents(keyword, limit=1):
    all_list = []
    page = 1
    while True:
        html = get_page(keyword, page=page)
        l = search_result(get_soup(html))
        if l == [] or page-1 == limit:
            break
        all_list.extend(l)
        page += 1

    return all_list

def make_content_dict(content) -> str:
    contents_data = {}
    url, title = search_contents_title(content)
    contents_data["title"] = title
    contents_data["url"] = url
    contents_data["tags"] = ", ".join(search_tags(content))
    contents_data["text"] = search_contents_text(content)
    return contents_data

def show(data):
    print(data["title"])
    print(data["url"])
    print(data["tags"])
    print(data["text"])
    print("\n")

def async_main():
    keyword = sys.argv[1]
    limit = sys.argv[2]

    for i, content in enumerate(async_get_all_contents(keyword, int(limit))):
        print(f"Contents: {i}")
        data = make_content_dict(content)
        print(f"Dictionary Data -> {data}\n")

def main():
    keyword = sys.argv[1]
    limit = sys.argv[2]

    for i, content in enumerate(get_all_contents(keyword, int(limit))):
        print(f"Contents: {i}")
        data = make_content_dict(content)
        print(f"Dictionary Data -> {data}\n")
        

if __name__ == "__main__":
    start = time.time()
    async_main()
    async_time = time.time() - start
    start = time.time()
    main()
    blocking_time = time.time() - start
    print(f"async_main(): {async_time}s\n"
          f"main()      : {blocking_time}s")