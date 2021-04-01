#!/usr/bin/env python
#
# Transifex impose a limit of maximum 2000 collaborators
# script to remove the users based on their last connection date

import json
import os
import requests
from urllib.parse import urljoin as j

# username/password stored in .env file
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

CSRFTOKEN = os.getenv('TRANSIFEX_CSRFTOKEN')
SESSIONID = os.getenv('TRANSIFEX_SESSIONID')

BASE_URL = "https://www.transifex.com/_/userspace/ajax/collaborators/"
HEADERS = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Content-Type': 'application/json',
    'DNT': '1',
    'X-Requested-With': 'XMLHttpRequest',
    'X-CSRFToken': CSRFTOKEN,
    'Origin': 'https://www.transifex.com',
    'Referer': 'https://www.transifex.com/odoo/collaborators/',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0',
    'Cookie': f'csrftoken={CSRFTOKEN}; sessionid={SESSIONID}',
}

def get_collaborators():
    # print("get_collaborators", page, query, roles, f"{BASE_URL}/odoo")
    print(j(BASE_URL, "odoo/ids/"))
    r = requests.post(j(BASE_URL, "odoo/ids/"), data='{}', headers=HEADERS)
    try:
        collaborator_ids = r.json()['data']
    except:
        with open('error-json.html', 'w') as f:
            f.write(r.text)
        print("error while fetching ids in error-json.html")
        return ''

    collaborators = []
    chunk_size = 20
    for i in range(0, len(collaborator_ids), chunk_size):
        print(f"... fetching chunk {i}...{i+chunk_size}")
        chunk_ids = collaborator_ids[i:i+chunk_size]
        r = requests.post(j(BASE_URL, "odoo/details/"), data='{"user_ids": %s}' % chunk_ids, headers=HEADERS)
        try:
            collaborators.extend(r.json()['data'])
        except:
            with open('error-json.html', 'w') as f:
                f.write(r.text)
            print("error while fetching details in error-json.html")
            return ''
    return collaborators

def remove_collatorator(user_id, username=False, reason='unknown'):
    print(f"Removing user {username or user_id} reason: {reason}")
    r = requests.post(j(BASE_URL, "remove/odoo/"),
        data=f'user_ids[]={user_id}',
        headers=dict(HEADERS, **{"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    )

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
    # import pudb;pu.db
    all_collabo = get_collaborators()
    old = []
    for col in all_collabo:
        # is_old = "10 months" in col['last_seen'] or "11 months" in col['last_seen']
        is_old = 'years' in col['last_seen']
        if is_old:
            print(f"{len(old)+1}: {col['username']} last seen {col['last_seen']}")
            if all(role in ['translator', 'reviewer'] for role in col['roles']):
                old.append(col)
            else:
                print(f" ... skipping as role: {', '.join(col['roles'])}")

    print(f"Can probably drop {len(old)} out of {len(all_collabo)}")

    with open('collaborators.json', 'w') as f:
        json.dump(all_collabo, f)
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
            remove_collatorator(u['user_id'], username=u['username'], reason=u['last_seen'])
            count += 1

    print(f"Removed {count} old contributors")

    # ids = [u['id'] for u in top_old[:10]]
    # print(remove_collatorators(ids))

list_all()
load_and_remove()
