
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from os import environ
from dotenv import load_dotenv

load_dotenv(override=True)

uri = environ["Database"]
 
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))['data']['data']

print(client.find_one({"name":"test"}))