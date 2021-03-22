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
    (r"^requirements.txt", "Packaging"),
    (r"^debian/.*", "Packaging"),
    (r"^addons/account.*", "Accounting"),
    (r"^account_.*", "Accounting"),
    (r".*\.po$", "Internationalization"),
    (r"^addons/mail/.*", "Discuss"),
    (r"^addons/hr.*", "HR"),
    (r"^hr_.*", "HR"),
    (r"^addons/fleet/.*", "HR"),
    (r"^l10n_.*_hr_payroll/.*", "HR"),
    (r"^industry_fsm.*_hr_payroll/.*", "HR"),
    (r"^addons/l10n_.*", "Localization"),
    (r"^l10n_.*", "Localization"),
    (r"^addons/stock.*", "Logistics"),
    (r"^addons/mrp.*", "Logistics"),
    (r"^stock_.*", "Logistics"),
    (r"^delivery_.*", "Logistics"),
    (r"^addons/crm.*", "Marketing"),
    (r"^addons/event.*", "Marketing"),
    (r"^addons/mass_mailing.*", "Marketing"),
    (r"^addons/website_slides.*", "Marketing"),
    (r"^event_.*", "Marketing"),
    (r"^helpdesk.*", "Marketing"),
    (r"^addons/point_of_sale/.*", "Point of Sale"),
    (r"^addons/pos_.*", "Point of Sale"),
    (r"^addons/sale.*", "Sales"),
    (r"^sale_.*", "Sales"),
    (r"^addons/payment.*", "Payment"),
    (r"^addons/website.*", "Website"),
    (r"^website_.*", "Website"),
    (r"^addons/web/static/src/js/.*", "Framework"),
    (r"^web_studio/.*", "Studio"),
    (r"^odoo/(models|fields).py", "ORM"),
    (r"^odoo/addons/base/models/ir_.*.py", "ORM"),
    (r"^odoo/osv/.*", "ORM"),
]
APP_LABELS_NAMES = [app[1] for app in APP_LABELS]


def rget(url, **kw):
    res = requests.get(url, headers={'Authorization': 'token '+os.getenv('GITHUB_TOKEN')}, **kw)
    if res.headers.get('x-ratelimit-remaining') == '0':
        print("Hit rate limit!")
        return None
    return res


def rpost(url, data, **kw):
    res = requests.post(url, json=data, headers={'Authorization': 'token '+os.getenv('GITHUB_TOKEN')}, **kw)
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
    for idx, file_info in enumerate(all_files):
        filename = file_info['filename']
        if filename.startswith("doc/cla"):
            labels.append(CLA_LABEL)
            all_files = all_files[:idx] + all_files[idx+1:]
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



def tag_prs(url):
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
        current_label_names = current_labels and [l['name'] for l in current_labels] or []
        # if not current_label_names:
        #     continue
        print("#%s: %s" % (pull['number'], pull['title']))
        if full_name == DEV_REPO:
            # not already tagged with R&D or OE
            if not (set(current_label_names) & set(TARGET_LABEL)):
                labels = guess_best_labels(pull)
                mark_label(pr_number, labels)
        else:
            # not already tagged with an app label
            if not(set(current_label_names) & set(APP_LABELS_NAMES)):
                labels = guess_app_labels(pr_number)
                if labels and set(labels) != set(current_label_names):
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
