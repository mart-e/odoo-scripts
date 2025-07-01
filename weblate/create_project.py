#!/usr/bin/env python

import os
import subprocess
import sys
import time
from pathlib import Path

import requests

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

BASE_URL = os.environ['WEBLATE_URL']
HEADERS = {"Authorization": f"Token {os.environ['WEBLATE_API_TOKEN']}", 'Content-Type': 'application/json', 'User-Agent': 'C3POdoo python-requests'}

ALL_COMPONENTS_URI = "/api/components/"
PROJECT_COMPONENTS_URI = "/api/projects/{project}/components/"
COMPONENT_URI = "/api/components/{project}/{component}/"

GET = lambda uri, **kw: requests.get(BASE_URL + uri, headers=HEADERS, **kw)
POST = lambda uri, **kw: requests.post(BASE_URL + uri, headers=HEADERS, **kw)
DELETE = lambda uri, **kw: requests.delete(BASE_URL + uri, headers=HEADERS, **kw)
PUT = lambda uri, **kw: requests.put(BASE_URL + uri, headers=HEADERS, **kw)

def scan_path(path: Path):
    if not path.exists():
        return []

    pots = []
    for d in path.iterdir():
        if not d.is_dir():
            continue
        if d.name.startswith('test') or d.name.startswith('l10n') or d.name.endswith('test'):
            continue

        if d.name in ["odoo", "addons"]:
            pots += scan_path(d)
        else:
            if (d / 'i18n' / f"{d.name}.pot").exists():
                pots.append(d)

    return pots

def get_components():
    r = GET(ALL_COMPONENTS_URI).json()
    #tot = r['count']  # TODO pagination
    return [c['slug'] for c in r['results']]

def create_component(path: Path, project, base_path):
    branch = subprocess.run("git symbolic-ref -q --short HEAD", shell=True, capture_output=True, cwd=str(base_path)) \
        .stdout \
        .decode() \
        .strip()
    local_path = str(path).split(str(base_path))[1][1:]  # odoo/addons/base

    r = POST(PROJECT_COMPONENTS_URI.format(project=project),
        json={
            "project": project,
            "name": f"o:odoo:p:{project}:r:{path.name}",
            "slug": path.name,
            "branch": branch,
            "vcs": "git",
            "file_format": "po",
            "new_base": f"{local_path}/i18n/{path.name}.pot",
            "filemask": f"{local_path}/i18n/*.po",
            "repo": "https://github.com/odoo/odoo",
    })
    if r.status_code != 201:
        return r.text
    return None

def create(path, project):
    base_path = Path(sys.argv[1]).resolve()
    pots = sorted(scan_path(base_path))
    project = sys.argv[2]
    components = get_components()
    
    print("Addons found:")
    for pot in pots:

        if pot.name not in components:
            print(f"{pot.name}: creating… ", end='', flush=True)
            t1 = time.time()
            error = create_component(pot, project, base_path)
            if error:
                print("ko:", error)
            else:
                print(f"ok ({int(time.time()-t1)}sec)")

        else:
            print(f"{pot.name}: skip")

def delete(project, component):
    print(f"Deleting component {project}/{component}")
    r = DELETE(COMPONENT_URI.format(project=project, component=component))
    if r.status_code != 204:
        print(r.status_code)
        print(r.text)

def shell():
    import pudb
    pudb.set_trace()


if __name__ == "__main__":
    usage = f"""Usage: {sys.argv[0]} [COMMAND]
commands:
  create [PATH] [PROJECT]
  delete [PROJECT] [COMPONENT]
  shell

args:
  PATH: path to the repository containing the translations
  PROJECT: slug of weblate project (i.e. odoo-18)
  COMPONENT: slug of weblate component (i.e. account), * for all"""
    if len(sys.argv) < 2:
        print(usage)
        sys.exit()

    command = sys.argv[1]
    if command == 'create':
        create(sys.argv[2], sys.argv[3])
    elif command == 'shell':
        shell()
    elif command == "delete":
        if sys.argv[3] == "*":
            for component in get_components():
                delete(sys.argv[2], component)
        else:
            delete(sys.argv[2], sys.argv[3])
    else:
        print(usage)
        sys.exit()

