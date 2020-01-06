#!/usr/bin/env python

import json
import os
import sys
import requests

from datetime import datetime, timedelta

from requests.auth import HTTPBasicAuth

# username/password stored in .env file
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

BASE_URL = "https://api.github.com/repos"

if len(sys.argv) > 1 and sys.argv[1].startswith('ent'):
    REPO = "odoo/enterprise"
    PR_FILE = 'github_old_pr_ent.json'
else:
    REPO = "odoo/odoo"
    PR_FILE = 'github_old_pr.json'

PULLS_URL = "%s/%s/pulls" % (BASE_URL, REPO)
PULL_URL = "%s/%s/pulls/%%s" % (BASE_URL, REPO)
ISSUE_URL = "%s/%s/issues/%%s" % (BASE_URL, REPO)
LABELS_URL = "%s/%s/issues/%%s/labels" % (BASE_URL, REPO)
COMMENT_URL = "%s/%s/issues/%%s/comments" % (BASE_URL, REPO)
UNSUPPORTED_BRANCH = ['7.0', '8.0', '9.0', '10.0', 'saas-15', 'saas-11', 'saas-18']

total = 0

AUTH = HTTPBasicAuth(os.getenv('GITHUB_USERNAME'), os.getenv('GITHUB_PASSWORD'))


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

def rpatch(url, data, **kw):
    res = requests.patch(url, json=data, auth=AUTH, **kw)
    if res.headers.get('x-ratelimit-remaining') == '0':
        print("Hit rate limit!")
        return None
    return res

def list_pr(url, version=False):
    global total
    global pr_info

    print("Get PR: %s" % url)
    params = {'state':'open'}
    if version:
        params['base'] = version
    res = rget(url, params=params)
    skip = True
    for pull in res.json():
        pr_number = str(pull['number'])

        if pr_info.get(pr_number):
            continue
        skip = False

        full_name = pull['head']['repo'] and pull['head']['repo']['full_name'] or 'unknown repository'
        pr_info[pr_number] = {
            'head': pull['head'],
            'number': pull['number'],
            'title': pull['title'],
            'full_name': full_name,
            'url': pull['url'],
            'user': pull['user'],
            'state': pull['state'],
            'base': pull['base']['ref'],
            'assignee': pull['assignee'],
            'author_association': pull['author_association'],
            'updated_at': pull['updated_at'],
        }
        info = pr_info[pr_number]

        if is_outdated(info):
            msg = get_closing_message(info)
            post_message(msg, info)
            close_pr(info)

    with open(PR_FILE, 'w') as f:
        json.dump(pr_info, f)

    if not skip and res.links.get('next'):
        return res.links['next']['url']
    return False


def is_outdated(info, recheck=False):
    if info['base'] not in UNSUPPORTED_BRANCH:
        print(f"  skip #{info['number']} as targetting {info['base']}")
        return False
    if info['state'] != 'open':
        return False
    if info['full_name'].startswith('odoo-dev'):
        print(f"...Skip #{info['number']} as from {info['full_name']}")
        return False
    if info['author_association'] not in ['CONTRIBUTOR', 'FIRST_TIME_CONTRIBUTOR']:
        print(f"...Skip #{info['number']} by a {info['author_association']}")
    # if info['assignee']:
    #     print(f"...Skip #{info['number']} as assigned to {info['assignee']['login']}")
    #     return False

    res = False
    if 'comments' not in info:
        url = PULL_URL % info['number']
        res = rget(url).json()
        info['comments'] = res['comments']
    if info['comments'] > 10:
        print(f"...Skip #{info['number']} as {info['comments']} comments")
        return False

    if recheck:
        if not res:
            url = PULL_URL % info['number']
            res = rget(url).json()
            info['updated_at'] = res['updated_at']
        if res['state'] != 'open':
            info['state'] = res['state']
            return False

    # if res['updated_at'] > (datetime.now() - timedelta(days=100)).isoformat():
    #     print(f"...Skip #{info['number']} as last updated {info['updated_at']}")
    #     return False

    print(f"Going to close PR #{info['number']} by @{info['user']['login']} targetting {info['base']}, last updated at {info['updated_at']}")
    return True

def get_closing_message(info):
    # return f"""Closing as version {info['base']} is no longer a supported version."""
    return f"""Dear @{info['user']['login']},

Thank you for your contribution but the version {info['base']} is no longer supported.
We only support the last 3 stable versions so no longer accepts patches into this branch.

We apology if we could not look at your request in time.
If the contribution still makes sense for the upper version, please let us know and do not hesitate to recreate one for the recent versions. We will try to check it as soon as possible.

_This is an automated message._
    """

def post_message(message, info):
    print(f"Post message to #{info['number']}")
    url = COMMENT_URL % info['number']
    res = rpost(url, {'body': message})
    return res.status_code

def close_pr(info):
    print(f"Close PR #{info['number']}")
    url = PULL_URL % info['number']
    res = rpatch(url, {'state': 'closed'})
    return res.status_code

def close_issue(info):
    print(f"Close PR #{info['number']}")
    url = ISSUE_URL % info['number']
    res = rpatch(url, {'state': 'closed'})
    return res.status_code

def close_outdated_pr():
    total = 0
    global pr_info
    for info in pr_info.values():
        if is_outdated(info, recheck=True):
            # print(f"Could close {info['number']}")
            msg = get_closing_message(info)
            post_message(msg, info)
            close_pr(info)
            total += 1
    print(f"Closed {total} old PR!")


if os.path.isfile(PR_FILE):
    with open(PR_FILE, 'r') as f:
        pr_info = json.loads(f.read())
else:
    pr_info = {}

res = list_pr(PULLS_URL, version='10.0')
while res:
    res = list_pr(res, version='10.0')
# close_outdated_pr()
