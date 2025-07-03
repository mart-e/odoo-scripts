#!/usr/bin/env python

import os
import sys
import time
from pathlib import Path

import requests

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
if not os.getenv('WEBLATE_API_TOKEN') and os.getenv('WEBLATE_URL'):
    print("Create a .env file containing at least WEBLATE_URL and WEBLATE_API_TOKEN")
    sys.exit()

BASE_URL = os.environ['WEBLATE_URL']
HEADERS = {"Authorization": f"Token {os.environ['WEBLATE_API_TOKEN']}", 'Content-Type': 'application/json', 'User-Agent': 'C3POdoo python-requests'}

ALL_COMPONENTS_URI = "/api/components/"
PROJECT_COMPONENTS_URI = "/api/projects/{project}/components/"
COMPONENT_URI = "/api/components/{project}/{component}/"

GET = lambda uri, **kw: requests.get(uri.startswith('/') and BASE_URL + uri or uri, headers=HEADERS, **kw)
POST = lambda uri, **kw: requests.post(uri.startswith('/') and BASE_URL + uri or uri, headers=HEADERS, **kw)
DELETE = lambda uri, **kw: requests.delete(uri.startswith('/') and BASE_URL + uri or uri, headers=HEADERS, **kw)
PUT = lambda uri, **kw: requests.put(uri.startswith('/') and BASE_URL + uri or uri, headers=HEADERS, **kw)

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
                if len(list((d / 'i18n').iterdir())) == 1:
                    # TODO can not pot if filemask i18n/*.po does not match any file
                    continue
                pots.append(d)

    return pots

def get_components(project=False):
    if project:
        uri = PROJECT_COMPONENTS_URI.format(project=project)
    else:
        uri = ALL_COMPONENTS_URI
    res = []
    while uri:
        r = GET(uri).json()
        res.extend([c['slug'] for c in r['results']])
        uri = r.get('next')
    return res

def create_component(project, path: Path, base_path, reference):
    local_path = str(path).split(str(base_path))[1][1:]  # odoo/addons/base

    if reference.startswith("git@") or reference.startswith("https://"):
        repo = reference
        # TODO branch !
    else:
        repo = f"weblate://{project}/{reference}"

    r = POST(PROJECT_COMPONENTS_URI.format(project=project),
        json={
            "project": project,
            "name": f"o:odoo:p:{project}:r:{path.name}",
            "slug": path.name,
            "file_format": "po",
            "new_base": f"{local_path}/i18n/{path.name}.pot",
            "filemask": f"{local_path}/i18n/*.po",
            "vcs": "git",
            "repo": repo,
            "template": "",
    })
    if r.status_code != 201:
        return r.text
    return None

def create(project, path, repo=False):
    base_path = Path(path).resolve()
    pots = sorted(scan_path(base_path))
    components = get_components(project)
    reference = False

    if not components and not repo:
        print("No existing components, specify reference repository")
        sys.exit()
    
    print("Addons found:")
    for pot in pots:
        if not reference and repo:
            # only one time
            reference = repo
        else:
            reference = sorted(list({p.name for p in pots} & set(components)))[0]

        if pot.name not in components:
            print(f"{pot.name}: creating… (ref {reference}) ", end='', flush=True)
            t1 = time.time()
            error = create_component(project, pot, base_path, reference)
            if error:
                print("ko:", error)
                break
            else:
                print(f"ok ({int(time.time()-t1)}sec)")
                components += pot.name

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
  create PROJECT PATH [GIT]
  delete PROJECT COMPONENT
  shell

args:
  COMPONENT: slug of weblate component (i.e. account), * for all
  GIT: url of the git repository to checkout
  PATH: path to the repository containing the translations
  PROJECT: slug of weblate project (i.e. odoo-18)"""
    if len(sys.argv) < 2:
        print(usage)
        sys.exit()

    command = sys.argv[1]
    if command == 'create':
        if len(sys.argv) == 5:
            project, path, repo = sys.argv[2:]
        else:
            project, path, repo = sys.argv[2], sys.argv[3], False
        create(project, path, repo)
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

