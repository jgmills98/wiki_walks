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
def wiki_curl(title, get_title=False):
    formatted_title = title.replace(" ","_")

    curl_url = wiki_url.format(formatted_title)

    req = requests.get(url=curl_url)

    req_result = bs4.BeautifulSoup(req.text,'html.parser')

    if "Wikipedia does not have an article with this exact name" in req_result.get_text():
        print("\"{}\" does not exist on Wikipedia. Please try fixing the capitalization or any other typo.".format(formatted_title))
        sys.exit()

    return req_result

def get_wiki_links(title):

    wiki_request = wiki_curl(title)

    req_result = wiki_request.find_all(id="mw-content-text")[0]

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

def get_title(title):

    wiki_request = wiki_curl(title)

    found_title = wiki_request.find(id="firstHeading")

    #title is stored like this in html page: "<h1 class="firstHeading" id="firstHeading" lang="en">Potato</h1>" 
    #grabs everything after ">" and before "</h1>"
    found_title = re.search('">(.+)(?=<\/h1>)', str(found_title))

    #wiki pages are underscore sperated for titles
    found_title = ("_").join(found_title.group(1).split(" "))

    return found_title

def get_links(title):

    query = check_db(title)

    if query == []:
        # print("{} not in db, doing wiki request".format(title))
        query = get_wiki_links(title)
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

    # db.drop()

    #check wiki to make get the real title (e.g. if ww2 is typed in, the actual title is World_War_II)
    actual_start = get_title(start)
    actual_end = get_title(end)

    run_search(actual_start, actual_end)

    data = get_wiki_links("Hello_Neighbor")
    print(data)

    # print(db.find_one({"name":"World_War_II"}))
    # check = check_db(db, "World_War_III")
    # print(check)

if __name__ == '__main__':
    main()