from label_studio_sdk.client import LabelStudio
import configparser
import json

config = configparser.ConfigParser()
config.read("config.ini")


LABEL_STUDIO_URL = config["LabelStudio"]["url"]
LABEL_STUDIO_API_KEY = config["LabelStudio"]["api_key"]
PROJECT_ID = 4

print(LABEL_STUDIO_URL)

ls = LabelStudio(base_url=LABEL_STUDIO_URL, api_key=LABEL_STUDIO_API_KEY)

tasks = ls.tasks.list(project=PROJECT_ID)
count = 0
for task in tasks:
    ls.tasks.delete(id=task.id)
    count+=1
print(f"Deleted {count} tasks")

with open('load.json', 'r', encoding='utf-8') as json_file:
    load_tasks = json.load(json_file)

ls.projects.import_tasks(id=PROJECT_ID, request=load_tasks)

print(f"Add {len(load_tasks)} tasks")