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
    ISSUE_FILE = 'github_old_issue_ent.json'
else:
    REPO = "odoo/odoo"
    PR_FILE = 'github_old_pr.json'
    ISSUE_FILE = 'github_old_issue.json'

# true = closing PR, false = closing issues
CLOSE_PR = True

PULLS_URL = "%s/%s/pulls" % (BASE_URL, REPO)
ISSUES_URL = "%s/%s/issues" % (BASE_URL, REPO)
PULL_URL = "%s/%s/pulls/%%s" % (BASE_URL, REPO)
ISSUE_URL = "%s/%s/issues/%%s" % (BASE_URL, REPO)
LABELS_URL = "%s/%s/issues/%%s/labels" % (BASE_URL, REPO)
COMMENT_URL = "%s/%s/issues/%%s/comments" % (BASE_URL, REPO)
SUPPORTED_BRANCH = ['16.0', '17.0', 'saas-17.2', 'saas-17.4', '18.0', 'saas-18.1', 'master']
MAX_AGE = 250
MAX_AGE_MEMBER = MAX_AGE * 2
MAX_AGE_MASTER = MAX_AGE * 5

total = 0
totals = {}

AUTH = HTTPBasicAuth(os.getenv('GITHUB_USERNAME'), os.getenv('GITHUB_TOKEN'))


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

def list_pr(url, version=False, close_old=True):
    global total
    global pr_info
    global totals

    print("Get PR: %s" % url)
    params = {'state':'open', 'per_page': 100, 'sort': 'updated', 'direction': 'asc'}
    if version:
        params['base'] = version
    res = rget(url, params=params)
    skip = True
    for pull in res.json():
        pr_number = str(pull['number'])

        # if pr_info.get(pr_number):
        #     continue
        skip = False
        if not pull.get("head"):
            print(pull)
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

        if close_old:
            if is_outdated(info, recheck=True):
                # print(f"Could close {info['number']}")
                msg = get_closing_message(info, is_pr=True)
                post_message(msg, info)
                close_pr(info)
        else:
            totals.setdefault(info['base'], 0)
            totals[info['base']] += 1

    with open(PR_FILE, 'w') as f:
        json.dump(pr_info, f)
    if not close_old:
        print(total)

    if not skip and res.links.get('next'):
        return res.links['next']['url']
    return False


def list_issue(url, close_old=True):
    global total
    print("Get Issues: %s" % url)
    params = {'state':'open', 'per_page': 100, 'sort': 'updated', 'direction': 'asc'}
    res = rget(url, params=params)
    skip = True
    for info in res.json():
        skip = False
        if info.get("pull_request"):
            continue

        if info["updated_at"] > (datetime.now() - timedelta(days=365*3)).isoformat():
            print(f"...Skip #{info['number']} as last updated {info['updated_at']}")
            continue

        msg = get_closing_message(info, is_pr=False)
        post_message(msg, info)
        close_issue(info)
        total += 1

    if not skip and res.links.get('next'):
        return res.links['next']['url']
    return False


def is_outdated(info, recheck=False):
    if info['base'] in SUPPORTED_BRANCH and info['base'] != 'master':
        #print(f"  skip #{info['number']} as targetting {info['base']}")
        return False
    if info['state'] != 'open':
        return False
    # if info['full_name'].startswith('odoo-dev'):
    #     print(f"...Skip #{info['number']} as from {info['full_name']}")
    #     return False
    # if info['author_association'] not in ['CONTRIBUTOR', 'FIRST_TIME_CONTRIBUTOR', 'NONE']:
    #print(f"...#{info['number']} is made by a {info['author_association']}")
    # if info['assignee']:
    #     print(f"...Skip #{info['number']} as assigned to {info['assignee']['login']}")
    #     return False

    res = False
    # if 'comments' not in info:
    #     url = PULL_URL % info['number']
    #     res = rget(url).json()
    #     info['comments'] = res['comments']
    # if info['comments'] > 10:
    #     print(f"...Skip #{info['number']} as {info['comments']} comments")
    #     return False

    if recheck:
        if not res:
            url = PULL_URL % info['number']
            res = rget(url).json()
            info['updated_at'] = res['updated_at']
        if res['state'] != 'open':
            info['state'] = res['state']
            return False

    if info['base'] == 'master':
        max_date = (datetime.now() - timedelta(days=MAX_AGE_MASTER)).isoformat()
    elif info['author_association'] == 'MEMBER':
        max_date = (datetime.now() - timedelta(days=MAX_AGE_MEMBER)).isoformat()
    else:
        max_date = (datetime.now() - timedelta(days=MAX_AGE)).isoformat()
    if res['updated_at'] > max_date:
        #print(f"...Skip #{info['number']} as last updated {info['updated_at']}")
        return False

    print(f"Going to close PR #{info['number']} by @{info['user']['login']} targetting {info['base']}, last updated at {info['updated_at']}")
    return True

def get_closing_message(info, is_pr=True):
    if is_pr:
        if info['base'] != 'master':
            return f"""Dear @{info['user']['login']},

Thank you for your contribution but the version {info['base']} is no longer supported.
We only support the last 3 stable versions so no longer accepts patches into this branch.

We apology if we could not look at your request in time.
If the contribution still makes sense for the upper version, please let us know and do not hesitate to recreate one for the recent versions. We will try to check it as soon as possible.

_This is an automated message._
    """
        else:
            return f"""Dear @{info['user']['login']},

Thank you for your contribution but we are closing it due to inactivity.

We apology if we could not look at your request in time.
If the contribution still makes sense, please let us know and do not hesitate to recreate one for the recent versions. We will try to check it as soon as possible.

_This is an automated message._
"""
    else:
        return f"""Dear @{info['user']['login']},

Thank you for your report but we are closing it due to inactivity.
We apology if we could not look at your request in time.
If your report still makes sense, don't hesitate to reopen a new one. We will try to check it as soon as possible.

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
    print(f"Close Issue #{info['number']}")
    url = ISSUE_URL % info['number']
    res = rpatch(url, {'state': 'closed'})
    return res.status_code

def close_outdated_pr():
    total = 0
    global pr_info
    for info in pr_info.values():
        if is_outdated(info, recheck=True):
            print(f"Could close {info['number']}")
            # msg = get_closing_message(info)
            # post_message(msg, info)
            # close_pr(info)
            total += 1
    print(f"Closed {total} old PR!")

if __name__ == "__main__":
    if CLOSE_PR:
        if False and os.path.isfile(PR_FILE):
            with open(PR_FILE, 'r') as f:
                pr_info = json.loads(f.read())
        else:
            pr_info = {}

        res = list_pr(PULLS_URL)
        while res:
            res = list_pr(res)
        print(total)
    else:
        res = list_issue(ISSUES_URL)
        while res:
            res = list_issue(res)
        print(total)
