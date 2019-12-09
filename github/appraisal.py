#!/usr/bin/env python3
# fetch activity of a user

import json
import os
import requests

from requests.auth import HTTPBasicAuth

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

BASE_URL = "https://api.github.com/users"

USER = 'mart-e'
EVENT_FILE = "github_events_%s.txt" % USER
EVENT_URL = "%s/%s/events" % (BASE_URL, USER)
MAIN_REPO = 'odoo/odoo'

AUTH = HTTPBasicAuth(os.getenv('GITHUB_USERNAME'), os.getenv('GITHUB_PASSWORD'))

MIN_DATE = "2018-02-01T00:00:00Z"
MAX_DATE = "2019-02-14T00:00:00Z"


total = {}
all_events = {}

def rget(url, **kw):
    res = requests.get(url, auth=AUTH, **kw)
    if res.headers.get('x-ratelimit-remaining') == '0':
        print("Hit rate limit!")
        return None
    return res


def rpost(url, data, **kw):
    res = requests.post(url, json=data, auth=AUTH, **kw)
    if res.headers.get('x-ratelimit-remaining') == '0':
        print("Hit rate limit!")
        return None
    return res


def list_events(url):
    global total
    global all_events

    print("Get events: %s" % url)
    res = rget(url, params={'state':'open'})
    stop = False
    for event in res.json():
        if event['id'] not in all_events:
            all_events[event['id']] = event
        date = event['created_at']

        if date > MAX_DATE:
            continue

        if date < MIN_DATE:
            stop = True
            break

        event_type = event['type']
        repo = event['repo']['name']
        total.setdefault(repo, {})
        total[repo].setdefault(event_type, 0)
        total[repo][event_type] += 1

        if event_type == 'PushEvent' and repo == MAIN_REPO:
            branch = event['payload']['ref'].split('/')[-1]
            message = event['payload']['commits'][0]['message'].split('\n')[0]
            print(f"{USER} pushed '{message}' on {branch}")

        if event_type == 'PullRequestEvent' and event['payload']['action'] == 'closed':
            total.setdefault('total_closed', 0)
            total['total_closed'] +=1
        elif event_type == 'PullRequestEvent':
            print(event['payload']['action'])

    with open(EVENT_FILE, 'w') as f:
        json.dump(all_events, f)

    if not stop and res.links.get('next'):
        return res.links['next']['url']
    return False

if os.path.isfile(EVENT_FILE):
    with open(EVENT_FILE, 'r') as f:
        all_events = json.loads(f.read())
else:
    all_events = {}

res = list_events(EVENT_URL)
while res:
    res = list_events(res)

print(f"User {USER} stats:")

print(json.dumps(total, sort_keys=True, indent=2))
