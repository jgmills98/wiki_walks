import requests
import bs4
import re
import argparse
#href="/wiki/.+?(?=\")"

wiki_url = "https://en.wikipedia.org/wiki/{}"

"href=/wiki/"

filter_list = [
    "#",
    "(disambiguation)",
    ".PNG",
    ".jpg",
    ".JPEG",
    ":NOTRS",
    "Template:",
    "Template_talk:",
    "Special:"
]


#curl requests to the wiki title and returns a set of all inter wiki links from that title
def wiki_curl(title):
    formatted_title = title.replace(" ","_")

    curl_url = wiki_url.format(formatted_title)

    req = requests.get(url=curl_url)
    req_result = bs4.BeautifulSoup(req.text,'html.parser').find_all(id="mw-content-text")[0]

    links = []

    for val in req_result.find_all('a', href=True):

        href_str = val.get('href')
        if any(x in href_str for x in filter_list) or not href_str.startswith("/wiki/"):
            continue

        links.append(href_str[6::])

    links = set(links)
    return links

def main():
    wiki_curl("World War II")

if __name__ == '__main__':
    #TODO: crete args for point A-B search
    main()
