#!/usr/bin/env python

import json
import os
import smtplib
import xmlrpc.client

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from requests.auth import HTTPBasicAuth

# username/password stored in .env file
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# file containing the repositories already found, to avoid spamming
OE_REPO_FILE = "/home/odoo/github_monitor/oe_repo_found.txt"
CODE_URL = "https://api.github.com/search/code"
COMMITS_URL = "https://api.github.com/repos/%s/%s/commits"
USER_URL = "https://api.github.com/users/%s/events"

SEARCH_CRITERIAS = "code_search_criterias.txt"

HEADERS={'Authorization': 'token '+os.getenv('GITHUB_TOKEN')}
RECIPIENT = "security@odoo.com"
RECIPIENT = "mat@openerp.com"
host = "www.odoo.com"
username = os.getenv("ODOO_LOGIN")
password = os.getenv("ODOO_PASSWORD")
port = "443"
db = "openerp"
if port in ("80", "443"):
    url = "%s://%s" % ("http" if port != "443" else "https", host)  # for saas instance
else:
    url = "http://%s:%s" % (host, port)  # for local instance


def rget(url, **kw):
    """ Make a GET request on a given URL """
    res = requests.get(url, headers=HEADERS, **kw)
    if res.headers.get("x-ratelimit-remaining") == "0":
        print("Hit rate limit!")
        return None
    return res.json()


def rpost(url, data, **kw):
    """ Make a POST request on a given URL """
    res = requests.post(url, json=data, headers=HEADERS, **kw)
    if res.headers.get("x-ratelimit-remaining") == "0":
        print("Hit rate limit!")
        return None
    return res.json()


def investigate_repo(murl):
    """ Guess repository owner based on github profile and last commits """
    user = murl.split("/")[3]
    repo = murl.split("/")[4]
    authors = []

    # first guess, look at previous push event commits
    r = rget(USER_URL % user)
    for index, event in enumerate(r):
        if event["type"] == "PushEvent":
            name = event["payload"]["commits"][0]["author"]["name"]
            email = event["payload"]["commits"][0]["author"]["email"]
            if (name, email) not in authors:
                authors.append((name, email))

    if not authors:
        # second guess, look at previous commits in the repository
        r = rget(COMMITS_URL % (user, repo))
        for index, commit in enumerate(r):
            if index > 5:
                break
            name = commit["commit"]["author"]["name"]
            email = commit["commit"]["author"]["email"]
            if (name, email) not in authors and not email.endswith("@odoo.com"):
                authors.append((name, email))

    res = {"authors": authors}
    if username and password:
        res.update(investigate_odoo_com(user, authors))
    return res


def investigate_odoo_com(user, authors):
    """ Find if the found authors are known """
    common = xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(url))
    models = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(url))
    uid = common.authenticate(db, username, password, {})
    github_users = models.execute_kw(
        db,
        uid,
        password,
        "openerp.enterprise.github.user",
        "search_read",
        [[("name", "ilike", user),]],
        {"fields": ["name", "subscription_id"]},
    )
    for gu in github_users:
        if gu["name"].lower() == user.lower():
            return {"subscriptions": gu}

    for name, email in authors:
        if not email or email in ["="]:
            continue
        partners = models.execute_kw(
            db,
            uid,
            password,
            "res.partner",
            "search_read",
            [[("email", "ilike", email),]],
            {"fields": ["name", "email", "sale_order_count"]},
        )
        for pa in partners:
            if pa["email"].lower() == email.lower():
                return {"odoo_author": pa}
    return {}


def search_occurrence(criteria):
    """ Search source code containing `criteria` """
    matches = []
    search_res = rget(CODE_URL, params={"q": search, "type": "Code"})
    if "total_count" not in search_res:
        return search_res["message"]

    if not search_res["total_count"]:
        return matches

    for item in search_res["items"]:
        rurl = item["repository"]["html_url"]  # short url
        murl = item["html_url"]  # full path to file that matched
        if rurl.startswith("https://github.com/odoo/"):
            # do not match on odoo's repositories
            continue

        if (
            murl.endswith("__manifest__.py")
            or murl.endswith(".md")  # name of the module in 'depends'
            or murl.endswith(".txt")  # documentation
            or murl.endswith(".rst")
            or murl.endswith(".csv")
            or murl.endswith(".html")
            or murl.endswith("MANIFEST.in")
        ):  # debian package
            continue

        matches.append((rurl, criteria, murl))

    return matches


def build_alert_email(alerts):
    sorted_matches = sorted(found.items(), key=lambda r: r[1][0], reverse=True)
    text = """Hi there,

The following github repositories have been found containing what may be enterprise code:
"""
    # first pass for repo
    for repo, match in sorted_matches:
        text += "\n* %s" % repo

    text += "\n\nDetails:\n"

    # second pass for details
    for repo, match in sorted_matches:
        nmatch, occurrences, authors = match

        for occurrence in occurrences:
            #                                 URL            criteria
            text += "\n * %s (matched %r)" % (occurrence[1], occurrence[0][:40])

        if authors.get("subscriptions"):
            text += "\n   odoo.com subscription:"
            sub = authors["subscriptions"]
            text += "\n     - "+sub['name']+": "+sub['subscription_id'][1]
        if authors.get("authors"):
            text += "\n   last commiters:"
            text += "\n     - "
            aut = authors["authors"]
            text += "\n     - ".join([(a + " (" + e + ")") for a, e in aut])
        if authors.get("odoo_author"):
            text += "\n   odoo.com res.partner:"
            author = authors["odoo_author"]
            text += "\n     - #%s %s <%s> (%s SO)" % (author['id'], author['name'], author['email'], author['sale_order_count'])
            # text += "\n     - ".join([(f"{aut['id']} {aut['name']} <{aut['email']}> (#{aut['sale_order_count']}SO)") for aut in auts])
        text += "\n"

    text += """

DMCA form:
https://github.com/contact/dmca-notice

This is an automatic message, the found repositories will appear only once per alert.
See https://github.com/odoo/support-tools/wiki/AutoMATion#enterprise for details.
"""
    return text


def send_alert_email(text, target=RECIPIENT):
    """ Send email altering of leaks """
    fromaddr = os.getenv("EMAIL_LOGIN")

    msg = MIMEMultipart()
    msg["From"] = fromaddr
    msg["To"] = target
    msg["Subject"] = "Copy of odoo/enterprise detected"
    msg.attach(MIMEText(text, "plain"))

    server = smtplib.SMTP(os.getenv("EMAIL_SERVER"), os.getenv("EMAIL_PORT"))
    server.ehlo()
    server.starttls()
    server.ehlo()
    #server.login(fromaddr, os.getenv("EMAIL_PASSWORD"))
    server.sendmail(fromaddr, target, msg.as_string())
    server.quit()


try:
    with open(OE_REPO_FILE, "r") as f:
        whitelist = f.read()
except FileNotFoundError:
    whitelist = ""


with open(SEARCH_CRITERIAS) as f:
    criterias = [l for l in f.read().splitlines() if not l.startswith("#")]

found = {}
for search in SEARCH_CRITERIAS:
    for (repo, criteria, murl) in search_occurrence(search):
        if repo in whitelist:
            continue

        # (repo, # match, occurences, authors)
        found.setdefault(
            repo,
            [
                0,
                [],
                {"authors": set([]), "subscriptions": {}, "odoo_author": {}},
            ],
        )
        found[repo][0] += 1
        found[repo][1].append((criteria, murl))

        authors = investigate_repo(murl)
        found[repo][2]["authors"] |= set(authors.get("authors", []))
        found[repo][2]["subscriptions"].update(authors.get("subscriptions", {}))
        found[repo][2]["odoo_author"].update(authors.get("odoo_author", {}))

if found:
    text = build_alert_email(found)
    send_alert_email(text)

    with open(OE_REPO_FILE, "a") as f:
        f.write("\n".join(found.keys()) + "\n")
