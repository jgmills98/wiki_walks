import json
from pymongo import MongoClient

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

def insert_db(title, data, collection):
    if collection == "items":
        elem = {"name": title, "links": data}
        db_items.insert_one(elem)
    elif collection == "results":
        elem = {"name": title, "data": data}
        db_results.insert_one(elem)