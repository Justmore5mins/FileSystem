
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from os import environ
from dotenv import load_dotenv

load_dotenv(override=True)

 
# Create a new client and connect to the server
db = MongoClient(environ['Database'], server_api=ServerApi('1'))['data']['data']

res = db.find()
l = [[k['name'], k['type'], k['content']] for k in res]
print(l)