#!/usr/bin/env python3
#
# Mark all unreviewed translations of a transifex project as reviewed
# usefull when you import the terms from another platerform

from hashlib import md5
import json
import os
import pickle
import requests

# username/password stored in .env file
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

APISERVER = "https://rest.api.transifex.com"
ORGANIZATION = "odoo"
PROJECT_NAME = "odoo-15"
TRANSIFEX_USERNAME = os.getenv('TRANSIFEX_USERNAME')
APITOKEN = os.getenv('TRANSIFEX_APITOKEN')

HEADERS = {
    "Authorization": f"Bearer {APITOKEN}",
    "Content-type": "application/vnd.api+json",
}

ALREADY_PROCESSED_MODULES_FILE = 'already_processed.bin'


def make_request(url, params=None, rtype="GET"):
    if rtype == "GET":
        response = requests.get(
            APISERVER + url,
            headers=HEADERS,
            params=params,
        )
    elif rtype == "PATCH":
        response = requests.patch(
            APISERVER + url,
            headers=HEADERS,
            data=params,
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


def mark_term_as_reviewed(resource, lang):
    strings = make_request("/resource_translations", params={
        "filter[resource]": f"o:{ORGANIZATION}:p:{PROJECT_NAME}:r:{resource}",
        "filter[language]": f"l:{lang}",
        "filter[translated]": "true",
        "filter[reviewed]": "false",
    })
    import pudb;pu.db
    print(f"Marking as reviewed {len(strings['data'])} for {resource} in {lang}")

    update_terms = []
    for term in strings["data"]:
        resource_id = term["id"]
        print(f"  {resource_id}")
        res = make_request(f"/resource_translations/{resource_id}",
            params={"data": {
                "attributes": {
                    "reviewed": "true",
                },
                "id": resource_id,
                "type": "resource_translations"
            }},
            rtype="PATCH")
        if res.get("errors"):
            print(res["errors"])
    #     source_entity_hash = get_source_entity_hash(term.get('key', ''), term.get('context', ''))
    #     update_terms.append({
    #         'translation': term.get('translation', ''),  # setting the existing translation is required, whyyy?
    #         'reviewed': True,
    #         'source_entity_hash': source_entity_hash
    #     })
    #     print("Marking %s terms for %s (%s) as reviewed" % (len(update_terms), resource, lang))
    # if update_terms:
    #     response = requests.put(
    #         SERVER + strings_url,
    #         data=json.dumps(update_terms),
    #         headers=HEADERS,
    #         auth=AUTH
    #     )
    #     response.raise_for_status()


def main(filter_lang):

    # getting all the languages
    project_id = f"o:{ORGANIZATION}:p:{PROJECT_NAME}"
    # langs_url = f"/projects/{project_id}/languages"
    # lang_entries = make_request(langs_url)

    # getting all the resources
    res_entries = make_request("/resources", params={
        "filter[project]": project_id
    })

    if os.path.exists(ALREADY_PROCESSED_MODULES_FILE):
        with open(ALREADY_PROCESSED_MODULES_FILE, 'rb') as f:
            already_processed_modules = pickle.load(f)
    else:
        already_processed_modules = {PROJECT_NAME:[]}
    for resource in res_entries["data"]:
        resource_name = resource["attributes"]["name"]
        if resource_name in already_processed_modules.get(PROJECT_NAME, []):
            continue
        # for lang in lang_entries:
        #     lang_name = lang['language_code']
        mark_term_as_reviewed(resource_name, filter_lang)
        already_processed_modules.append(resource_name)
        with open(ALREADY_PROCESSED_MODULES_FILE, 'wb') as f:
            pickle.dump(already_processed_modules, f, protocol=2)


if __name__ == '__main__':
    main("nl")
