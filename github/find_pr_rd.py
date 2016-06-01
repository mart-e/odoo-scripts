#!/usr/bin/env python

import json
import os
import requests

from requests.auth import HTTPBasicAuth
from urlparse import urljoin

BASE_URL = "https://api.github.com/repos"
REPO = "odoo/odoo"
PULLS_URL = "%s/%s/pulls" % (BASE_URL, REPO)
LABELS_URL = "%s/%s/issues/%%s/labels" % (BASE_URL, REPO)

total = 0

AUTH = HTTPBasicAuth('USERNAME', 'PASSWORD')


PR_FILE = 'github_pr.json'


def rget(url, **kw):
    res = requests.get(url, auth=AUTH, **kw)
    if res.headers.get('x-ratelimit-remaining') == '0':
        print "Hit rate limit!"
        return None
    return res


def rpost(url, data, **kw):
    res = requests.post(url, json=data, auth=AUTH, **kw)
    if res.headers.get('x-ratelimit-remaining') == '0':
        print "Hit rate limit!"
        return None
    return res


def guess_best_labels(pull):
    branch = pull['head']['ref'].lower()
    title = pull['title'].lower()
    body = pull['body'].lower()
    if 'opw' in branch or \
        'opw' in title or \
        'opw' in body:
        return ['OE']
    if 'migration' in branch or \
        'newapi' in branch or \
        'new-api' in branch or \
        'migration' in title or \
        'new api' in title or \
        'migration' in body or \
        'new api' in body:
        return ['MigrationNewAPI', 'RD']
    return ['RD']


def mark_label(pr_number, labels):
    print "Set labels %s on #%s" % (', '.join(labels), pr_number)
    label_url = LABELS_URL % pr_number
    res = rpost(label_url, labels)
    return res.status_code


def get_prs(url):
    global total
    global pr_info

    print "Get PR: %s" % url
    res = rget(url, params={'state':'open'})
    for pull in res.json():
        pr_number = str(pull['number'])

        if pr_info.get(pr_number):
            continue

        full_name = pull['head']['repo'] and pull['head']['repo']['full_name'] or 'unknown repository'
        pr_info[pr_number] = {
            'head': pull['head'],
            'number': pull['number'],
            'title': pull['title'],
            'url': pull['url'],
            'full_name': full_name,
            'user': pull['user']['login'],
            'state': pull['state'],
            'number': pull['number'],
        }

        if full_name == 'odoo-dev/odoo':
            total += 1
            print "#%s (%s): %s" % (pull['number'], total, pull['title'])

            label_url = LABELS_URL % pr_number
            labels = rget(label_url).json()
            pr_info[pr_number]['labels'] = labels
            if not labels:
                labels = guess_best_labels(pull)
                mark_label(pr_number, labels)

    with open(PR_FILE, 'w') as f:
        json.dump(pr_info, f)

    if res.links.get('next'):
        return res.links['next']['url']
    return False


if os.path.isfile(PR_FILE):
    with open(PR_FILE, 'r') as f:
        pr_info = json.loads(f.read())
else:
    pr_info = {}

res = get_prs(PULLS_URL)
while res:
    res = get_prs(res)
