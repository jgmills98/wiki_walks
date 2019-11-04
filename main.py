import requests
import bs4
import re
import json
import sys
import queue

from urllib.parse import unquote
from pymongo import MongoClient

from util import *

#href="/wiki/.+?(?=\")"

wiki_url = "https://en.wikipedia.org/wiki/{}"

"href=/wiki/"

filter_list = [
    "#",
    "(disambiguation)",
    ".PNG",
    ".jpg",
    ".svg",
    ".JPEG",
    ":NOTRS",
    "Template:",
    "Template_talk:",
    "Special:",
    "File:",
    "Category:CS1_maint:_archived_copy_as_title",
    "Help:",
    "Wikipedia:Citation_needed",
    "Wikipedia:"
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
        #remove url encoding from string
        href_str = unquote(href_str)

        if any(x in href_str for x in filter_list) or not href_str.startswith("/wiki/"):
            continue

        if href_str[6::] not in links:
            links.append(href_str[6::])

    return links

def get_links(title):

    query = check_db(title)

    if query == []:
        # print("{} not in db, doing wiki request".format(title))
        query = wiki_curl(title)
        insert_db(title, query)
        return query
    else:
        # print("{} in db".format(title))
        return query["links"]
    
def run_search(start, end):
    print(start,end)
    
    traveled = {}

    qu = queue.Queue()
    qu.put(start)

    connected_title = start

    depth_array = []

    n = 0
    depth_index = 0
    depth = 0

    while(not qu.empty()):
        print(qu.qsize())

        query_title = qu.get()

        if query_title in traveled:
            n += 1
            continue

        print("Currently in {} connected by {}".format(query_title, connected_title))

        traveled[query_title] = 1

        results = get_links(query_title)

        if n == 0:
            last_title = results[-1]
            connected_title = query_title
            next_title = results[0]

        # print(len(results))

        if end in results:
            print("Connected {} to {} in {} clicks".format(start, end, depth))
            break

        if last_title == query_title:
            depth += 1
            last_title = results[-1]
            connected_title = next_title
            next_title = results[0]


        for item in results:
            qu.put(item)
        
        if n == 3000:
            print(qu.qsize())
            break
        
        n += 1

def main():
    start = sys.argv[1]
    end = sys.argv[2]

    run_search(start, end)
    wiki_curl("World War II")

if __name__ == '__main__':
    #TODO: crete args for point A-B search
    main()