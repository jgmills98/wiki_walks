import json
from pymongo import MongoClient


def open_json(file):
    with open("{}.json".format(file)) as json_file:
        json_data = json.load(json_file)
        return json_data

def connect_db(config):
    client = MongoClient(config["db_url"])
    return client["wikidb"].items

config = open_json("config")
db = connect_db(config)

#searches database for name that matches the title
def check_db(title):
    query_res = db.find_one({"name":title})
    if query_res:
        return query_res
    else:
        return []

def insert_db(title, data):
    elem = {"name": title, "links": data}
    db.insert_one(elem)