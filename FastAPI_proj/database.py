import pymongo

mongoURI = "mongodb://localhost:27017"
client = pymongo.MongoClient(mongoURI)

db = client["MEDIA"]
collection = db["USER"]
collection2 = db["POSTS"]


def create_user(data):
    data = dict(data)
    response = collection.insert_one(data)
    return str(response.inserted_id)


def all_user():
    response = collection.find({})
    data = []
    for i in response:
        i["_id"] = str(i["_id"])
        data.append(i)
    return list(data)


def all_post():
    response = collection2.find({})
    data = []
    for i in response:
        i["_id"] = str(i["_id"])
        data.append(i)
    return list(data)


def get_user(condition):
    response = collection.find_one({"user__id": condition})
    if response:
        return condition
    return condition + 1


def get_username(condition):
    response = collection.find_one({"username": condition})
    if response:
        return condition
    return condition + "1"

def get_userdetail(condition):
    response = collection.find_one({"username": condition})
    if response:
        return response
    return None


def create_post(data):
    data = dict(data)
    response = collection2.insert_one(data)
    return str(response.inserted_id)


def get_post(condition):
    response = collection2.find_one({"post_id": condition})
    if response:
        return condition
    return condition + 1


def like(id):
    data = collection2.find_one({"post_id": id})
    data = dict(data)
    response = collection2.update_one({"post_id": data["post_id"]}, {"$set": {"likes": data["likes"] + 1}})
    return response


def comment(com, id):
    data = collection2.find_one({"post_id": id})
    data = dict(data)
    response = collection2.update_one({"post_id": data["post_id"]}, {"$set": {"comment": data["comment"] + [com]}})
    return response

def get_userid_byname(condition):
    response = collection.find_one({"username": condition})
    data = dict(response)
    return data["user__id"]