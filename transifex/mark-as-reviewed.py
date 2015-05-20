#!/usr/bin/env python3
# hey works also in python2, so vintage
#
# Mark all unreviewed translations of a transifex project as reviewed
# usefull when you import the terms from another platerform

from hashlib import md5
import requests
import json
import pickle

SERVER = "https://www.transifex.com"
PROJECT_NAME = "odoo-80"
TRANSIFEX_USERNAME = "alice"
TRANSIFEX_PASSWORD = "b0b"

AUTH = (TRANSIFEX_USERNAME, TRANSIFEX_PASSWORD)
HEADERS = {'Content-type': 'application/json'}

ALREADY_PROCESSED_MODULES_FILE = 'already_processed.txt'


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
    strings_url = "/api/2/project/%s/resource/%s/translation/%s/strings/" % (PROJECT_NAME, resource, lang)
    strings = requests.get(
        SERVER + strings_url,
        headers=HEADERS,
        auth=AUTH
    ).json()

    update_terms = []
    for term in strings:
        if term.get('reviewed') or not term.get('translation'):
            continue
        source_entity_hash = get_source_entity_hash(term.get('key', ''), term.get('context', ''))
        update_terms.append({
            'translation': term.get('translation', ''),  # setting the existing translation is required, whyyy?
            'reviewed': True,
            'source_entity_hash': source_entity_hash
        })
    print("Marking %s terms for %s (%s) as reviewed" % (len(update_terms), resource, lang))
    if update_terms:
        response = requests.put(
            SERVER + strings_url,
            data=json.dumps(update_terms),
            headers=HEADERS,
            auth=AUTH
        )
        response.raise_for_status()


def main():

    # getting all the languages
    langs_url = "/api/2/project/%s/languages/" % PROJECT_NAME

    lang_entries = requests.get(
        SERVER + langs_url,
        headers=HEADERS,
        auth=AUTH
    ).json()

    # getting all the resources
    res_url = "/api/2/project/%s/resources/" % PROJECT_NAME
    res_entries = requests.get(
        SERVER + res_url,
        headers=HEADERS,
        auth=AUTH
    ).json()

    with open(ALREADY_PROCESSED_MODULES_FILE, 'rb') as f:
        already_processed_modules = pickle.load(f)
    for resource in res_entries:
        resource_name = resource['name']
        if resource_name in already_processed_modules:
            continue
        for lang in lang_entries:
            lang_name = lang['language_code']
            mark_term_as_reviewed(resource_name, lang_name)
        already_processed_modules.append(resource_name)
        with open(ALREADY_PROCESSED_MODULES_FILE, 'wb') as f:
            pickle.dump(already_processed_modules, f, protocol=2)


if __name__ == '__main__':
    main()
