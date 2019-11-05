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

    found_title = wiki_request.find(id="firstHeading").text

    #wiki pages are underscore sperated for titles
    found_title = ("_").join(found_title.split(" "))

    return found_title

def get_links(title):

    query = check_db(title, "items")

    if query == []:
        # print("{} not in db, doing wiki request".format(title))
        query = get_wiki_links(title)
        insert_db(title, query, "items")
        return query
    else:
        # print("{} in db".format(title))
        return query["links"]

#checks if the query has been ran before
def check_search(start, end):
    name_str = start + " " + end
    check = check_db(name_str, "results")
    return check
    
def run_search(start, end):
    
    print("Finding \"{}\" from \"{}\"".format(end, start))

    sentinal_node = None
    
    traveled = {}

    parent_dict = {}

    qu = queue.Queue()
    qu.put(start)
    qu.put(sentinal_node)

    depth = 0
    n = 0

    while(not qu.empty()):
        # print(qu.qsize())
        
        query_title = qu.get()

        if query_title == sentinal_node:
            depth += 1
            #dont add another sentinal if the queue is already empty
            if qu.qsize() != 0:
                qu.put(sentinal_node, sentinal_node)
            continue

        if query_title == end:
            print("Found {} in {} clicks".format(end, depth))
            break

        #check if we have seen this title before
        if query_title in traveled:
            continue
        
        #add title to traveled dict
        traveled[query_title] = 1

        results = get_links(query_title)

        if end in results:
            parent_dict[end] = query_title
            print("Found \"{}\" in {} clicks".format(end, depth))
            break  

        for res in results:
            if res not in parent_dict:
                parent_dict[res] = query_title
            qu.put(res)

    route = find_route(parent_dict, start, end)

    store_result(start, end, depth, route)

    return route, depth

def store_result(start, end, depth, route):
    data = {}
    name = "{} {}".format(start, end)
    data["depth"] = depth
    data["route"] = route
    insert_db(name, data, "results")
    return

def find_route(parent_dict, start, end):
    route_list = []
    curr = end
    route_list.append(end)

    while curr != start:
        parent = parent_dict[curr]
        route_list.append(parent)
        curr = parent

    return route_list[::-1]

def print_info(start, end, depth, route):
    print("It took {} clicks to go from {} -> {}".format(depth, start, end))
    print("The route taken was:")
    print(" -> ".join(route))

def print_q(que):
    while not que.empty():
        print(que.get())

def get_result_data(data):
    depth = data["data"]["depth"]
    route = data["data"]["route"]
    return route, depth

def main():
    start = sys.argv[1]
    end = sys.argv[2]

    #check wiki to make get the real title (e.g. if ww2 is typed in, the actual title is World_War_II)
    actual_start = get_title(start)
    actual_end = get_title(end)

    check = check_search(actual_start, actual_end)

    if check == []:
        route, depth = run_search(actual_start, actual_end)
    else:
        print("Route already done, displaying previous results")
        route, depth = get_result_data(check)

    print_info(actual_start, actual_end, depth, route)


if __name__ == '__main__':
    main()