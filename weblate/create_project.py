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

COMPONENTS_URI = "/api/components/"
COMPONENT_URI = "/api/projects/{project}/components/"


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
    r = requests.get(BASE_URL + COMPONENTS_URI, headers=HEADERS).json()
    #tot = r['count']  # TODO pagination
    return [c['slug'] for c in r['results']]

def create_component(path: Path, project, base_path):
    branch = subprocess.run("git symbolic-ref -q --short HEAD", shell=True, capture_output=True, cwd=str(base_path)) \
        .stdout \
        .decode() \
        .strip()
    local_path = str(path).split(str(base_path))[1][1:]  # odoo/addons/base

    r = requests.post(BASE_URL + COMPONENT_URI.format(project=project),
        headers=HEADERS,
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


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} [PATH] [PROJECT]\n  PATH: path to the repository containing the translations\n  PROJECT: slug of weblate project (i.e. odoo-18)")
        sys.exit()

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
