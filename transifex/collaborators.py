#!/usr/bin/env python
#
# Transifex impose a limit of maximum 2000 collaborators
# script to remove the users based on their last connection date

import json
import os
import requests

# username/password stored in .env file
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

CSRFTOKEN = os.getenv('TRANSIFEX_CSRFTOKEN')
SESSIONID = os.getenv('TRANSIFEX_SESSIONID')

BASE_URL = "https://www.transifex.com/_/userspace/ajax/collaborators"
HEADERS = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'DNT': '1',
    'X-Requested-With': 'XMLHttpRequest',
    'Host': 'www.transifex.com',
    'Referer': 'https://www.transifex.com/odoo/collaborators/?',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Cookie': f'csrftoken={CSRFTOKEN}; sessionid={SESSIONID};',
    'X-CSRFToken': '41dzkee6jsfdlv79twkw8feivz4j4xkv'
}

collaborators = []
old = []

def get_collaborators(page=1, query='', roles=''):
    # print("get_collaborators", page, query, roles, f"{BASE_URL}/odoo")
    r = requests.get(f"{BASE_URL}/odoo/", params={
        'page': page,
        'query': query,
        'roles': roles,
        'mode': 'full',
    }, headers=HEADERS)

    try:
        return r.json()
    except:
        with open('error-json.html', 'w') as f:
            f.write(r.text)
        print("error")
        return ''

def remove_collatorator(user_id, username=False, reason='unknown'):
    print(f"Removing user {username or user_id} reason: {reason}")
    r = requests.post(f"{BASE_URL}/remove/odoo/", 
        data={'user_ids[]': user_id},
        headers=HEADERS)

    try:
        return r.json()
    except:
        with open('error-json.html', 'w') as f:
            f.write(r.text)
        print("error", r.text[:40])
        return ''

def remove_collatorators(user_ids):
    print(f"Removing users {user_ids}")
    print('&'.join([f'user_ids[]={user_id}' for user_id in user_ids]))
    r = requests.post(f"{BASE_URL}/remove/odoo/", 
        data='&'.join([f'user_ids[]={user_id}' for user_id in user_ids]),
        headers=HEADERS)

    try:
        return r.json()
    except:
        with open('error-json.html', 'w') as f:
            f.write(r.text)
        print("error", r.text[:40])
        return ''


def list_all():
    r = get_collaborators()
    previous_id = False
    max_page = r['pages']
    # max_page = 175
    for page in range(1, max_page):
        r = get_collaborators(page)
        for col in r['collaborators']:
            if previous_id == col['id']:
                # duplicated
                continue
            previous_id = col['id']
            # is_old = "10 months" in col['last_seen'] or "11 months" in col['last_seen']
            is_old = 'years' in col['last_seen']
            if is_old:
                print(f"{len(old)}: {col['username']} last seen {col['last_seen']}")
                if all(role in ['translator', 'reviewer'] for role in col['roles']):
                    old.append(col)
                else:
                    print(f" ... skipping as role: {', '.join(col['roles'])}")
            collaborators.append(col)

    print(f"Can probably drop {len(old)} out of {len(collaborators)}")

    with open('collaborators.json', 'w') as f:
        json.dump(collaborators, f)
    with open('collaborators-old.json', 'w') as f:
        json.dump(old, f)


def load_and_remove():
    with open('collaborators-old.json', 'r') as f:
    # with open('collaborators.json', 'r') as f:
        old = json.load(f)

    count = 0
    sorted_old = sorted(old, key=lambda d: d['last_seen'], reverse=True)

    for u in sorted_old:
        # if u['username'].startswith("gtc_") and "months" in u['last_seen']:
            remove_collatorator(u['id'], username=u['username'], reason=u['last_seen'])
            count += 1

    print(f"Removed {count} old contributors")

    # ids = [u['id'] for u in top_old[:10]]
    # print(remove_collatorators(ids))

list_all()
load_and_remove()
