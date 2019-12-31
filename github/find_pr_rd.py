#!/usr/bin/env python

import json
import os
import re
import sys
import requests

from requests.auth import HTTPBasicAuth

# username/password stored in .env file
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

BASE_URL = "https://api.github.com/repos"

if len(sys.argv) > 1 and sys.argv[1].startswith('ent'):
    REPO = "odoo/enterprise"
    DEV_REPO = 'odoo-dev/enterprise'
    PR_FILE = 'github_pr_ent.json'
else:
    REPO = "odoo/odoo"
    DEV_REPO = 'odoo-dev/odoo'
    PR_FILE = 'github_pr.json'

PULLS_URL = "%s/%s/pulls" % (BASE_URL, REPO)
LABELS_URL = "%s/%s/issues/%%s/labels" % (BASE_URL, REPO)
FILES_URL = "%s/%s/pulls/%%s/files" % (BASE_URL, REPO)
COMMENT_URL = "%s/%s/issues/%%s/comments" % (BASE_URL, REPO)
IGNORED_LABELS = ['8.0', '9.0', '10.0', '11.0', '12.0']
TARGET_LABEL = ['RD', 'OE']
CLA_LABEL = "CLA"
APP_LABELS = [
    ("^addons/account.*", "Accounting"),
    (".*\.po$", "Internationalization"),
    ("^addons/mail/.*", "Discuss"),
    ("^addons/hr.*", "HR"),
    ("^hr_.*", "HR"),
    ("^addons/fleet/.*", "HR"),
    ("^l10n_.*_hr_payroll/.*", "HR"),
    ("^industry_fsm.*_hr_payroll/.*", "HR"),
    ("^addons/l10n_.*", "Localization"),
    ("^l10n_.*", "Localization"),
    ("^addons/stock.*", "Logistics"),
    ("^addons/mrp.*", "Logistics"),
    ("^addons/crm.*", "Marketing"),
    ("^addons/event.*", "Marketing"),
    ("^addons/point_of_sale/.*", "Point of Sale"),
    ("^addons/pos_.*", "Point of Sale"),
    ("^addons/sale.*", "Sales"),
    ("^addons/payment.*", "Sales"),
    ("^addons/website.*", "Website"),
]
APP_LABELS_NAMES = [app[1] for app in APP_LABELS]

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


def guess_best_labels(pull):
    branch = pull['head']['ref'].lower()
    title = pull['title'].lower()
    body = (pull['body'] or '').lower()
    if 'opw' in branch or \
        'opw' in title or \
        'opw' in body:
        return ['OE']
    return ['RD']

def guess_app_labels(pr_number):
    files_url = FILES_URL % pr_number
    # don't use pagination but if more than 20 files, probably not worth tagging anyway
    all_files = rget(files_url).json()
    labels = []
    matched_regex, matched_label = False, False

    # make a first pass on cla as compatible with other tags
    for file_info in all_files:
        filename = file_info['filename']
        if filename.startswith("doc/cla"):
            labels.append(CLA_LABEL)
            break

    for file_info in all_files:
        filename = file_info['filename']
        if matched_regex:
            if not re.match(matched_regex, filename):
                # not full match, give up
                return labels
            # still matching, next file
            continue

        # several regex may match the same label, needs to check all
        for regex, label in APP_LABELS:
            if re.match(regex, filename):
                if not matched_label:
                    matched_label = label
                    break
                elif matched_label == label:
                    # still matching, next file
                    break
                else:
                    # not full match, give up
                    return labels
        else:
            # made 0 match, better not tag anything
            return labels
    if matched_label:
        labels.append(matched_label)
    return labels


def mark_label(pr_number, labels):
    print("Set labels %s on #%s" % (', '.join(labels), pr_number))
    label_url = LABELS_URL % pr_number
    res = rpost(label_url, labels)
    return res.status_code

def list_pr(url, version='7.0'):
    global total
    global pr_info

    print("Get PR: %s" % url)
    res = rget(url, params={'state':'open'})
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
            'url': pull['url'],
            'full_name': full_name,
            'user': pull['user']['login'],
            'state': pull['state'],
            'number': pull['number'],
            'base': pull['base']['ref'],
            'author_association': pull['author_association'],
            'assignee': pull['assignee'],
            'updated_at': pull['updated_at'],
        }

        if full_name == DEV_REPO:
            total += 1
            print("#%s (%s): %s" % (pull['number'], total, pull['title']))

            label_url = LABELS_URL % pr_number
            labels = rget(label_url).json()
            label_names = labels and [l['name'] for l in labels] or []
            pr_info[pr_number]['labels'] = labels
            # no label or none of the targetted ones
            if not label_names or not (set(label_names) & set(TARGET_LABEL)):
                labels = guess_best_labels(pull)
                mark_label(pr_number, labels)

    with open(PR_FILE, 'w') as f:
        json.dump(pr_info, f)

    if not skip and res.links.get('next'):
        return res.links['next']['url']
    return False


def tag_prs(url):
    global total
    global pr_info

    print("Get PR: %s" % url)
    res = rget(url, params={'state':'open'})
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
            'url': pull['url'],
            'full_name': full_name,
            'user': pull['user']['login'],
            'state': pull['state'],
            'number': pull['number'],
            'base': pull['base']['ref'],
            'author_association': pull['author_association'],
            'assignee': pull['assignee'],
            'updated_at': pull['updated_at'],
        }

        label_url = LABELS_URL % pr_number
        current_labels = rget(label_url).json()
        pr_info[pr_number]['labels'] = current_labels
        label_names = current_labels and [l['name'] for l in current_labels] or []
        if not label_names:
            continue
        print("#%s (%s): %s" % (pull['number'], total, pull['title']))
        total += 1
        if full_name == DEV_REPO:
            # not already tagged with R&D or OE
            if not (set(label_names) & set(TARGET_LABEL)):
                labels = guess_best_labels(pull)
                mark_label(pr_number, labels)
        else:
            # not already tagged with an app label
            if not(set(label_names) & set(APP_LABELS_NAMES)):
                labels = guess_app_labels(pr_number)
                if labels:
                    mark_label(pr_number, labels)

    with open(PR_FILE, 'w') as f:
        json.dump(pr_info, f)

    if not skip and res.links.get('next'):
        return res.links['next']['url']
    return False

def stats_per_branches():
    with open(PR_FILE, 'r') as f:
        stats = json.load(f)

    branches = {}
    for pr in stats.values():
        br = pr['base']
        branches.setdefault(br, 0)
        branches[br] += 1
    print(branches)

if os.path.isfile(PR_FILE):
    with open(PR_FILE, 'r') as f:
        pr_info = json.loads(f.read())
else:
    pr_info = {}

res = tag_prs(PULLS_URL)
while res:
    res = tag_prs(res)
