import json
import requests

# DUMMY_JSON_URL = "https://dummyjson.com/posts?limit=10"
API_SERVICE = "https://3a4dv94r2h.execute-api.eu-central-1.amazonaws.com/prod/items"

with open("data.json") as f:
    json_data = json.load(f)["posts"]

request_body = dict()
posts_length = len(json_data)

for i, post in enumerate(json_data):
    request_body["title"] = post["title"]
    request_body["description"] = post["body"]
    resp = requests.post(API_SERVICE, json=request_body)
    print(f"[{i+1}/{posts_length}]: {resp.status_code}, {resp.content}")
