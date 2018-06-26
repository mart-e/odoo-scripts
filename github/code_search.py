#!/usr/bin/env python

import os
import requests

from requests.auth import HTTPBasicAuth
from pprint import pprint

# username/password stored in .env file
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


BASE_URL = "https://api.github.com/search/code"

SEARCH_CRITERIAS = [
    'odoo',
]

AUTH = HTTPBasicAuth(os.getenv('GITHUB_USERNAME'), os.getenv('GITHUB_PASSWORD'))


def rget(url, **kw):
    """ Make a GET request on a given URL """
    res = requests.get(url, auth=AUTH, **kw)
    if res.headers.get('x-ratelimit-remaining') == '0':
        print("Hit rate limit!")
        return None
    return res.json()


def rpost(url, data, **kw):
    """ Make a POST request on a given URL """
    res = requests.post(url, json=data, auth=AUTH, **kw)
    if res.headers.get('x-ratelimit-remaining') == '0':
        print("Hit rate limit!")
        return None
    return res.json()


found = {}
for search in SEARCH_CRITERIAS:
    search_res = rget(BASE_URL, params={'q': search, 'type': 'Code'})
    if not search_res['total_count']:
        continue

    for item in search_res['items']:
        rurl = item['repository']['html_url']
        murl = item['html_url']  # full path to file that matched
        if rurl.startswith("https://github.com/odoo/"):
            # do not match on odoo's repositories
            continue

        if (murl.endswith('__manifest__.py') or  # name of the module in 'depends'
            murl.endswith('README.md') or  # documentation
            murl.endswith('.txt') or
            murl.endswith('.rst') or
            murl.endswith('MANIFEST.in')):  # debian package
            continue

        found.setdefault(rurl, [0, set()])
        found[rurl][0] += 1
        found[rurl][1].add(search)

sorted_matches = sorted(found.items(), key=lambda r: r[1][0], reverse=True)
for match in sorted_matches:
    print(f"{match[0]}\n\tmatched {match[1][0]} time(s) ({', '.join(match[1][1])})")
