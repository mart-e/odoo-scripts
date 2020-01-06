#!/usr/bin/env python

import os
import requests
import subprocess
from werkzeug.urls import url_quote_plus

# username/password stored in .env file
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

APISERVER = "https://api.transifex.com"
ORGANIZATION = "odoo"
PROJECT_NAME = "odoo-13"
PROJECT_NAME = "odoo-master"
PATH_TO_ADDONS = "/home/mat/odoo/documentation-user"
PATH_TO_ADDONS = "/home/mat/odoo/odoo/addons"
PATH_TO_ENT = "/home/mat/odoo/enterprise"

VERSION = "saas-13.1"
RAW_URL = "https://raw.githubusercontent.com/%s/documentation-user/%s/locale/sources/{module}.pot" % (ORGANIZATION, VERSION)
RAW_URL = "https://raw.githubusercontent.com/%s/odoo/%s/addons/{module}/i18n/{module}.pot" % (ORGANIZATION, VERSION)

CSRFTOKEN = os.getenv('TRANSIFEX_CSRFTOKEN')
SESSIONID = os.getenv('TRANSIFEX_SESSIONID')
TRANSIFEX_USERNAME = os.getenv('TRANSIFEX_USERNAME')
# TRANSIFEX_PASSWORD = os.getenv('TRANSIFEX_PASSWORD')
APITOKEN = os.getenv('TRANSIFEX_APITOKEN')

# AUTH = (TRANSIFEX_USERNAME, TRANSIFEX_PASSWORD)
AUTH = ('api', APITOKEN)
HEADERS = {
    'Content-type': 'application/json'
}



def make_api_request(url, params=False):
    print("  req ", url, params)
    response = requests.get(
        APISERVER + url,
        headers=HEADERS,
        auth=AUTH,
        params=params
    )
    try:
        return response.json()
    except ValueError:
        # probably got throttled, sorry for the spam Transifex
        print(response.text)
        return []


def get_source_entity_hash(key, context):
    """Term access url is the MD5 of 'key:context' """
    if isinstance(context, list):
        if context:
            keys = [key] + context
        else:
            keys = [key, '']
    else:
        if context:
            keys = [key, context]
        else:
            keys = [key, '']
    return str(md5(':'.join(keys).encode('utf-8')).hexdigest())


def get_resources_id():
    strings_url = f"/organizations/{ORGANIZATION}/projects/{PROJECT_NAME}/resources/"
    done = False
    offset = 0
    strings = []
    while not done:
        if offset:
            r = make_api_request(strings_url, {'offset': offset})
        else:
            r = make_api_request(strings_url)
        if len(r) < 100:
            done = True
        offset += 100
        strings.extend(r)

    resources = {}

    for resource in strings:
        resources[resource['name']] = resource['id']

    return resources


res = get_resources_id()
tx_addons = set(res.keys())
commu_addons = set(os.listdir(PATH_TO_ADDONS))
ent_addons = set(os.listdir(PATH_TO_ENT))

orphan_resources = tx_addons - commu_addons - ent_addons
if orphan_resources:
    print("Resources that are still on Transifex but not found locally:")
    print(orphan_resources)

for addons_path in sorted(os.listdir(PATH_TO_ADDONS)):
    if not res.get(addons_path):
        if 'l10n' not in addons_path:
            print(f"   missing resource {addons_path}")
        continue

    print(f"processing {addons_path}...")
    raw_url = url_quote_plus(RAW_URL.format(module=addons_path))
    print(RAW_URL.format(module=addons_path))
    subprocess.run(
f"curl 'https://www.transifex.com/_/resources/ajax/{ORGANIZATION}/{PROJECT_NAME}/content/autofetch/' -H 'Host: www.transifex.com' "
f"-H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0' -H 'Accept: */*' "
f"-H 'Accept-Language: en-US,en;q=0.5' -H 'Referer: https://www.transifex.com/{ORGANIZATION}/{PROJECT_NAME}/content/' "
f"-H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' -H 'X-CSRFToken: {CSRFTOKEN}' "
f"-H 'X-Requested-With: XMLHttpRequest' "
f"-H 'Cookie: csrftoken={CSRFTOKEN}; sessionid={SESSIONID};' "
f"-H 'DNT: 1' -H 'Connection: keep-alive' "
f"--data 'csrfmiddlewaretoken={CSRFTOKEN}&url={raw_url}&res_id={res[addons_path]}'",
        shell=True)
