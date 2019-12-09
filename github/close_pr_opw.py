#!/usr/bin/env python

import os
import sys
import xmlrpc.client
import requests

from requests.auth import HTTPBasicAuth

# username/password stored in .env file
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

BASE_URL = "https://api.github.com/repos"

if len(sys.argv) > 1 and sys.argv[1].startswith('ent'):
    REPO = "odoo/enterprise"
else:
    REPO = "odoo/odoo"
    # REPO = "mart-e/openerp"

PULLS_URL = "%s/%s/pulls" % (BASE_URL, REPO)
PULL_URL = "%s/%s/pulls/%%s" % (BASE_URL, REPO)
ISSUE_URL = "%s/%s/issues/%%s" % (BASE_URL, REPO)
LABELS_URL = "%s/%s/issues/%%s/labels" % (BASE_URL, REPO)
COMMENT_URL = "%s/%s/issues/%%s/comments" % (BASE_URL, REPO)
host = 'www.odoo.com'
username = os.getenv('ODOO_LOGIN')
password = os.getenv('ODOO_PASSWORD')
port = '443'
db = 'openerp'
if port in ('80', '443'):
    xmlrpc_url = '%s://%s' % ('http' if port != '443' else 'https', host)  # for saas instance
else:
    xmlrpc_url = 'http://%s:%s' % (host, port)  # for local instance

AUTH = HTTPBasicAuth(os.getenv('GITHUB_USERNAME'), os.getenv('GITHUB_PASSWORD'))

OPW_TO_PR = {

}

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

def investigate_odoo_com(opw_ids):
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(xmlrpc_url))
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(xmlrpc_url))
    uid = common.authenticate(db, username, password, {})
    return models.execute_kw(db, uid, password, 'project.task', 'search_read', [[
        ('id', 'in', opw_ids),
    ]], {'fields': ['name', 'stage_id']})

def get_closing_message(info, issue=None):
    if not issue:
        return f"""Dear @{info['user']['login']},

_This is an automated message._
This issue is linked to an Odoo support ticket that has been closed.
We hope you got an answer to your issue.

If you believe the problem is not solved yet and would like to keep this issue open, please let us know to reopen it.
"""

    return f"""Dear @{info['user']['login']},

_This is an automated message._
This issue is linked to the Odoo support ticket opw-{issue['id']} that has been closed.
We hope you got an answer to your issue.

If you believe the problem is not solved yet and would like to keep this issue open, please let us know to reopen it.
"""

def post_message(message, info):
    print(f"Post message to {REPO}#{info['number']}")
    pr_url = COMMENT_URL % info['number']
    res = rpost(pr_url, {'body': message})
    return res.status_code

def close_pr(info):
    print(f"Close PR {REPO}#{info['number']}")
    pr_url = PULL_URL % info['number']
    res = rpatch(pr_url, {'state': 'closed'})
    return res.status_code

def close_issue(info):
    print(f"Close issue {REPO}#{info['number']}")
    gh_url = ISSUE_URL % info['number']
    res = rpatch(gh_url, {'state': 'closed'})
    return res.status_code

def close_opw_pr(pr_opws):
    issues = investigate_odoo_com(list(pr_opws))
    cpt = 0
    for issue in issues:
        pr_number = pr_opws[issue['id']]
        if issue['stage_id'][1] not in ['Done', 'Cancelled', 'Cancelled (PS)']:
            print(f"Skip {REPO}#{pr_number} as opw-{issue['id']} in state {issue['stage_id'][1]}")
            continue

        gh_url = ISSUE_URL % pr_number
        info = rget(gh_url).json()
        if info.get('message'):
            print(gh_url, info['message'])
            continue

        if info['state'] != 'open':
            print(f"Skip {REPO}#{pr_number} as in state {info['state']}")
            continue

        print(f"Issue {REPO}#{pr_number} (opw-{issue['id']}) to be closed")
        cpt += 1
        msg = get_closing_message(info, issue)
        post_message(msg, info)
        close_issue(info)
    print(cpt)

def search_opw_pr():
    prs = rget(PULLS_URL, params={'filter': 'OPW'}).json()
    for pr in prs:
        print(pr['number'])
        print(pr['body'])
        print()

# close_opw_pr(OPW_TO_PR)
search_opw_pr()
