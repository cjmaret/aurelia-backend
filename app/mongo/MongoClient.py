from pymongo import MongoClient
from app.config import Config

def get_mongo_client():
    mongo_uri = Config.MONGO_URI
    client = MongoClient(mongo_uri)
    return client
