import json
import  time
import random
from pymongo import MongoClient
import pymongo

def open_json(file):
    with open("{}.json".format(file)) as json_file:
        json_data = json.load(json_file)
        return json_data

def connect_db(config, collection):
    client = MongoClient(config["db_url"])

    if collection == "items":
        return client["wikidb"].items
    elif collection == "results":
        return client["wikidb"].results

config = open_json("config")
db_items = connect_db(config, "items")
db_results = connect_db(config, "results")


#searches database for name that matches the title
def check_db(title, collection):
    try:
        if collection == "items":
            query_res = db_items.find_one({"name":title})
            if query_res:
                return query_res
            else:
                return []

        elif collection == "results":
            query_res = db_results.find_one({"name":title})
            if query_res:
                return query_res
            else:
                return []
    except pymongo.errors.AutoReconnect:
        "DB disconnect. Waiting 15 seconds before reconnecting"
        time.sleep(15)
        return check_db(title, collection)

def insert_db(title, data, collection):
    if collection == "items":
        elem = {"name": title, "links": data}
        db_items.insert_one(elem)
    elif collection == "results":
        elem = {"name": title, "data": data}
        db_results.insert_one(elem)

#searched for items with the title in its list and deletes it from the db
def reverse_delete(title):
    query = {"links":{"$all":[title]}}

    search = db_items.find(query)
    for item in search:
        name = item["name"]
        print("Deleting: {} from db".format(name))
        db_items.delete_one({"name":name})
    # db_items.delete_many(query)
    query = {"name":title}
    print("Deleting: {} from db".format(title))
    db_items.delete_one(query)

def get_db_size():
    return db_items.count()

def get_n_titles(n):

    # db_size = get_db_size()
    # rand_int = random.randint(0,db_size-1)
    rand_titles = db_items.aggregate([{"$sample":{"size":n}}])
    title_list = []
    for title in rand_titles:
        title_list.append(title["name"])

    return title_list
    