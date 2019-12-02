import requests
import bs4
import re
import json
import sys
import queue
import argparse
import re
import random
import numpy as np

from urllib.parse import unquote
from pymongo import MongoClient

from util import *

#href="/wiki/.+?(?=\")"

wiki_url = "https://en.wikipedia.org/wiki/{}"
random_url = "https://en.wikipedia.org/wiki/Special:Random"

"href=/wiki/"

perc_placeholder = "**___**"

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
    "Wikipedia:",
    "Several",
    "Alt=icon",
    "User:"
]

#curl requests to the wiki title and returns a set of all inter wiki links from that title
def wiki_curl(title, get_title=False, random=False):
    formatted_title = title.replace(" ","_")

    curl_url = wiki_url.format(formatted_title) if random == False else random_url

    req = requests.get(url=curl_url)
    req_result = bs4.BeautifulSoup(req.text,'html.parser')
    
    # if "Wikipedia does not have an article with this exact name" in req_result.get_text():
    #     print("\"{}\" does not exist on Wikipedia. Please try fixing the capitalization or any other typo.".format(formatted_title))
    #     sys.exit()

    if get_title == True:
        found_title = req_result.find(id="firstHeading").text
        if "% " in found_title:
            perc_index = found_title.find("%")
            found_title = found_title[:perc_index + 1] + "25" + found_title[perc_index + 1:]
        
        #wiki pages are underscore sperated for titles
        found_title = ("_").join(found_title.split(" "))

        return found_title


    return req_result

def get_wiki_links(title):
    if "%_" in title:
        perc_index = title.find("%_")
        title = title[:perc_index + 1] + "25" + title[perc_index + 1:] 

    wiki_request = wiki_curl(title)

    req_result = wiki_request.find_all(id="mw-content-text")[0]

    links = []

    for val in req_result.find_all('a', href=True):
        
        href_str = val.get('href')


        if "%25" in href_str:
            href_str = href_str.replace("%25",perc_placeholder)
        
        #remove url encoding from string
        href_str = unquote(href_str)

        if perc_placeholder in href_str:
            href_str = href_str.replace(perc_placeholder, "%25")

        if re.search(r"\%\$(\w+)\%",href_str):
            continue

        if any(x in href_str for x in filter_list) or not href_str.startswith("/wiki/"):
            continue

        if href_str[6::] not in links:
            links.append(href_str[6::])

    return links

def get_title(title):
    print(title)
    wiki_request = wiki_curl(title)

    found_title = wiki_request.find(id="firstHeading").text
    if "% " in found_title:
        perc_index = found_title.find("%")
        found_title = found_title[:perc_index + 1] + "25" + found_title[perc_index + 1:]
    
    #wiki pages are underscore sperated for titles
    found_title = ("_").join(found_title.split(" "))

    return found_title

def get_links(title):

    #check if query already has been done, if not get result from wiki and cache it in the db
    query = check_db(title, "items")

    if query == []:
        query = get_wiki_links(title)
        insert_db(title, query, "items")
        return query
    else:
        return query["links"]

#checks if the query has been ran before
def check_search(start, end):
    name_str = start + " " + end
    check = check_db(name_str, "results")
    return check

def get_n_random(n):
    print("Getting {} random pages".format(n))
    low = 100
    med = 300
    high = 500

    lowc = 0
    medc = 0
    highc = 0


    rand_list = []
    done = False
    while done == False:
        rand_title = wiki_curl("",True,True)
        title_links_size = len(get_wiki_links(rand_title))
        
        if title_links_size <= low:
            if lowc <= (n/3)-1:
                lowc += 1
                print(lowc,medc,highc)

        elif title_links_size > low and title_links_size <= med:
            if medc <= (n/3)-1:
                medc += 1
                print(lowc,medc,highc)

        elif title_links_size > med:
            if highc <= (n/3)-1:
                highc += 1
                print(lowc,medc,highc)

        rand_list.append(rand_title)

        if lowc == n/3 and medc == n/3 and highc == n/3:
            done = True
            
    return rand_list

def run_search(start, end, max_depth):
    if start == end:
        return [],0

    print("Finding \"{}\" from \"{}\"".format(end, start))

    sentinal_node = None

    traveled = {}

    parent_dict = {}

    qu = queue.Queue()
    qu.put(start)
    qu.put(sentinal_node)

    depth = 0
    n = 0
    exit_loop = False

    while(not qu.empty()):
        if depth == max_depth+1:
            return [], -1

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

        print("{} {} {} {}".format(n, query_title, qu.qsize(), depth))
        n += 1

        #add title to traveled dict
        traveled[query_title] = 1
        try:
            results = get_links(query_title)
        except IndexError:
            reverse_delete(query_title)
            parent = parent_dict[query_title]
            new_links = get_links(parent)
            fix_arr = []
            while not qu.empty():
                fix_arr.append(qu.get())
            for link in new_links:
                qu.put(link)
            for link in fix_arr:
                qu.put(link)
            continue

        deleted = False
        for res in results:
            if "% " in res or "%_" in res:

                perc_index = res.find("%")
                res = res[:perc_index + 1] + "25" + res[perc_index + 1:]
                if deleted == False:
                    db_items.delete_one({"name":query_title})
                    deleted = True
                    print("deleting {} from db because of {}".format(query_title, res))
                # sys.exit()


            if res == end:
                parent_dict[end] = query_title
                print("Found \"{}\" in {} clicks".format(end, depth))
                exit_loop = True
                break

            if res not in parent_dict:
                parent_dict[res] = query_title
                qu.put(res)

        if exit_loop:
            break

    route = find_route(parent_dict, start, end)
    print("n: {}".format(n))
    store_result(start, end, depth, route)

    return route, depth

def iterative_deep(start, end, depth):
    return

def matrix_calc(n, max_depth):
    titles = get_n_random(n)
    # print(titles)
    matrix = np.zeros((n,n))
    for i in range(0,n):
        for j in range(0,n):
            check = check_search(titles[i], titles[j])

            if check == []:
                route, depth = run_search(titles[i], titles[j], max_depth)
            else:
                route, depth = get_result_data(check)

            # route,depth = run_search(titles[i],titles[j], max_depth)
            if depth == -1:
                matrix[i][j] = 0
            else:
                matrix[i][j] = 1
    print(titles)
    for row in matrix:
        print(row)

    results = []
    for row in matrix:
        count = 0
        for item in row:
            count += item
        results.append(count/n)
    print(results)

    return

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

def get_args():
    arg = argparse.ArgumentParser()
    arg.add_argument("--start", required=True)
    arg.add_argument("--end", required=True)
    arg.add_argument("-r", "--requery", action="store_true", default=False)
    return arg.parse_args()

def main():
    # args = get_args()
    # print(args)

    #check wiki to make get the real title (e.g. if ww2 is typed in, the actual title is World_War_II)
    # actual_start = get_title(args.start)
    # actual_end = get_title(args.end)

    # check = check_search(actual_start, actual_end)

    # if check == [] or args.requery == True:
    #     route, depth = run_search(actual_start, actual_end)
    # else:
    #     print("Route already done, displaying previous results")
    #     route, depth = get_result_data(check)

    # print_info(actual_start, actual_end, depth, route)

    # iterative_deep(actual_start, actual_end, 1)

    matrix_calc(45,2)
    # print(get_n_random(10))

if __name__ == '__main__':
    main()