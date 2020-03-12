#!/usr/bin/env python3
#
# install module and languages to compute db size

import argparse
import base64
import getpass
import subprocess

import xmlrpc.client as xmlrpclib
import os
import glob
from os.path import expanduser as e

# connection information
host = "127.0.0.1"
port = 8069

uid = None
url = "%s://%s:%s" % (
    "http" if port != 443 else "https",
    host,
    port,
)  # for local instance
# url = '%s://%s' % ('http' if port != 443 else 'https', host)  # for saas instance


def install_modules(modules, db, username, password):
    common = xmlrpclib.ServerProxy("{}/xmlrpc/2/common".format(url))
    uid = common.authenticate(db, username, password, {})

    models = xmlrpclib.ServerProxy("{}/xmlrpc/2/object".format(url))

    module_ids = models.execute_kw(
        db,
        uid,
        password,
        "ir.module.module",
        "search",
        [
            [
                ("name", "like", "theme_"),
                ("name", "!=", "theme_common"),
                ("name", "not in", modules),
                ("state", "!=", "uninstalled"),
            ]
        ],
    )
    if module_ids:
        models.execute_kw(
            db,
            uid,
            password,
            "ir.module.module",
            "button_immediate_uninstall",
            [module_ids],
        )

    module_ids = models.execute_kw(
        db,
        uid,
        password,
        "ir.module.module",
        "search",
        [[("name", "in", modules), ("state", "!=", "installed")]],
    )
    print("module_ids", module_ids)
    if module_ids:
        models.execute_kw(
            db,
            uid,
            password,
            "ir.module.module",
            "button_immediate_install",
            [module_ids],
        )


def activate_lang(langs, db, username, password):
    common = xmlrpclib.ServerProxy("{}/xmlrpc/2/common".format(url))
    uid = common.authenticate(db, username, password, {})
    models = xmlrpclib.ServerProxy("{}/xmlrpc/2/object".format(url))

    for lang_code in langs:
        install_id = models.execute_kw(
            db, uid, password, "base.language.install", "create", [{"lang": lang_code}],
        )
        models.execute_kw(
            db, uid, password, "base.language.install", "lang_install", [[install_id]]
        )


def get_table_size(db):
    subprocess.call(
        """echo "VACUUM ANALYZE" | psql %s"""
        % db,
        shell=True,
    )
    subprocess.call(
        """echo "SELECT pg_size_pretty(pg_table_size('ir_translation')) AS table_size,
                        pg_size_pretty(pg_indexes_size('ir_translation')) AS indexes_size,
                        pg_size_pretty(pg_total_relation_size('ir_translation')) AS total_size" | psql %s"""
        % db,
        shell=True,
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--database", required=True, help="the name of the database to use"
    )
    parser.add_argument(
        "-l", "--login", default="admin", help="user account, default 'admin'"
    )
    parser.add_argument(
        "-p",
        "--password",
        help="password of the user, default 'admin', using prompt if login but no user is specified",
    )
    parser.add_argument('-i', '--install', action='store_true',
                        help='install modules before exporting')


    args = parser.parse_args()

    if args.login == "admin" and not args.password:
        args.password = "admin"
    if not args.password:
        args.password = getpass.getpass(f"Password for user {args.login}: ")

    if args.install:
        modules = ["crm", "sale", "project", "hr_expense", "website_event", "survey", "website_slides"]
        install_modules(modules, args.database, args.login, args.password)

        langs = ["fr_FR", "nl_BE", "es_ES", "zh_CN", "de_DE", "it_IT", "uk_UA"]
        activate_lang(langs, args.database, args.login, args.password)

    get_table_size(args.database)
