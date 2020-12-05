import time
import sys

import requests
from bs4 import BeautifulSoup

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

def search_contents_text(soup):
    contents = soup.find("div", class_="searchResult_snippet")
    return contents.text.replace("\n", "")

def get_all_contents(keyword, limit=1):
    all_list = []
    page = 1
    while True:
        html = get_page(keyword, page=page)
        l = search_result(get_soup(html))
        if l == [] or page-1 == limit:
            break
        all_list.extend(l)
        time.sleep(1)
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

def main():
    keyword = sys.argv[1]
    limit = sys.argv[2]

    for i, content in enumerate(get_all_contents(keyword, int(limit))):
        print(f"Contents: {i}")
        data = make_content_dict(content)
        print(f"Dictionary Data -> {data}\n")
        # show(data)
        

if __name__ == "__main__":
    main()