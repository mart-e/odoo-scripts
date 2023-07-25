#!/usr/bin/env python3
#
# install and export the terms of all odoo modules

from os.path import expanduser as e
import xmlrpc.client as xmlrpclib

import argparse
import base64
import getpass
import glob
import os
import subprocess
import polib

# connection information
host = '127.0.0.1'
port = 8069

# paths to community and enterprise modules
BASE_MODULE_PATH = [e('~/odoo/odoo/openerp/addons/base/i18n'), e('~/odoo/odoo/odoo/addons/base/i18n')]
ADDONS_PATH = e('~/odoo/odoo/addons/')
TXPATH = e('~/odoo/odoo/.tx/config')
ENT_ADDONS_PATH = e('~/odoo/enterprise/')
ENT_TXPATH = e('~/odoo/enterprise/.tx/config')
THEME_PATH = e('~/odoo/design-themes/')
THEME_TXPATH = e('~/odoo/design-themes/.tx/config')
TX_BIN = "/home/mat/odoo/tx"

l = set([os.path.basename(os.path.dirname(i)) for i in glob.glob(os.path.join(ADDONS_PATH, '*/__init__.py'))])
# without 'web' as is in enterprise and breaks if more than one 'theme_'
ADDONS_1 = sorted([i for i in l if (
    ('l10n_' not in i or i == 'l10n_multilang') and
    'theme_' not in i and
    'hw_' not in i and
    'test' not in i and
    'ldap' not in i
    #not i.startswith('payment_')
# )]
)] + ['base'])

ADDONS_2 = sorted(list({i for i in l if (
    ('l10n_be' in i) and
    'test' not in i and 'ldap' not in i)} - set(ADDONS_1)))

l = glob.glob(os.path.join(ENT_ADDONS_PATH, '*/__init__.py'))
ENT_ADDONS_1 = [os.path.basename(os.path.dirname(i)) for i in l if (
    ('l10n_' not in i) and
    'theme_' not in i and
    'pos_blackbox_be' not in i and
    'test' not in i
    # os.path.basename(os.path.dirname(i)) != 'sale_ebay'
)]
ENT_ADDONS_2 = sorted(list(set([os.path.basename(os.path.dirname(i)) for i in l if (
    ('l10n_be' in i) and
    'test' not in i)]) - set(ENT_ADDONS_1)))

# ENT_ADDONS_BE_PAYROLL = [os.path.basename(os.path.dirname(i)) for i in l if (
#     'l10n_be_hr_payroll' in i and
#     'test' not in i
# )]

l = glob.glob(os.path.join(THEME_PATH, '*/__init__.py'))
THEME_ADDONS_1 = [os.path.basename(os.path.dirname(i)) for i in l]

MODULES_TO_EXPORT = []

uid = None


def generate_tx_config(addons_path, tx_path, project, modules_list):
    """ generate the .tx/config file based on list of addons

    WARNING if a .pot file is empty, the module should be removed manually from
    this file (otherwise tx client will complain)
    $ ls -lh addons/*/i18n/*.pot | grep 432
    """
    l = glob.glob(addons_path+'*/__init__.py')
    modules = list(set(os.path.basename(os.path.dirname(i)) for i in l))
    if 'base' in modules_list:
        modules.append('base')
    modules.sort()

#     configf = open(tx_path, 'w')
#     configf.write("""[main]
# host = https://www.transifex.com

# """)

    prepath = ''
    if tx_path == TXPATH:
        prepath = 'addons/'

    for m in modules:
        # if (m.startswith('l10n_') and m != 'l10n_multilang') or \
        #         m.startswith('hw_') or m.startswith('test_') or m.endswith('_test'):
        # # if project == 'l10n_be_hr_payroll' and 'l10n_be_hr_payroll' not in m:
        #     continue
        if m not in modules_list:
            print(f"Skip {m} as not in modules_list")
            continue

        if m == "base":
            fname = "odoo/addons/base/i18n/base.pot"
        else:
            fname = "%s%s/i18n/%s.pot" % (prepath, m, m)

        if not os.path.exists(fname):
            print(f"Skip {fname} as not .pot")
            continue

        try:
            print(f"Generate tx for {fname}")
            p = polib.pofile(fname)
            if len(p) <= 2:
                print(f"Skip {fname} as too small")
                continue
        except:
            pass

        file_filter = "odoo/addons/base/i18n/<lang>.po" if m == "base" else f"{prepath}{m}/i18n/<lang>.po"
        subprocess.call([TX_BIN, "add",
            "--organization", "odoo",
            "--project", project,
            "--resource", m,
            "--resource-name", m,
            "--file-filter", file_filter,
            "--type", "PO",
            fname])

#         if m == 'base':
#             configf.write("""[o:odoo:p:%s:r:base]
# file_filter = odoo/addons/base/i18n/<lang>.po
# source_file = odoo/addons/base/i18n/base.pot
# source_lang = en

# """ % project)
#             continue


#         configf.write("""[o:odoo:p:%s:r:%s]
# file_filter = %s%s/i18n/<lang>.po
# source_file = %s
# source_lang = en

# """ % (project, m, prepath, m, fname))

#     configf.close()


def install_modules(modules, db, username, password, uninstall_incompatible=False):
    common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    print("Logged in as %s (uid: %d)" % (username, uid))

    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    if uninstall_incompatible:
        module_ids = models.execute_kw(db, uid, password, 'ir.module.module', 'search',  [[
            '|', ('name', 'like', 'theme_'), ('name', 'like', 'l10n_'), ('name', '!=', 'theme_common'), ('name', 'not in', modules), ('state', '!=', 'uninstalled')]])
        if module_ids:
            models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_uninstall',  [module_ids])

    module_ids = models.execute_kw(db, uid, password, 'ir.module.module', 'search',  [[('name', 'in', modules), ('state', '!=', 'installed')]])
    # module_ids = models.execute_kw(db, uid, password, 'ir.module.module', 'search',  [[('name', 'in', modules)]])
    print("installing", modules)
    print("module_ids", module_ids)
    if module_ids:
        models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_install',  [module_ids])


def export_terms(modules, addons_path, db, username, password):
    """ generate all .pot files

    WARNING check release.py version info or can be corrected with
    $ sed -i 's/Odoo Server 9.0alpha1/Odoo Server 9.0/g' addons/*/i18n/*.pot

    could also be useful to remove "empty" changes
    $ git status --short | grep '.pot' | sed 's/^ M *//' | xargs -I {} bash -c 'if test `git diff {} | grep "^+" | grep -v "^+++\|^+#\|POT-Creation-Date\|PO-Revision-Date" | wc -l` -eq 0; then git checkout -- {}; fi'
    """

    common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    print("Logged in as %s (uid: %d)" % (username, uid))

    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    modules = models.execute_kw(db, uid, password, 'ir.module.module', 'search_read',  [
        [
            ('state', '=', 'installed'),
            ('name', 'in', modules),
        ],
        ['name']])
    print("Exporting", modules)
    for module in modules:
        m_id = module['id']
        m_name = module['name']

        print("Export module %s" % m_name)
        export_id = models.execute_kw(db, uid, password, 'base.language.export', 'create',  [{
            'lang': '__new__',
            'format': 'po',
            'modules': [[6, False, [m_id]]],
            'state': 'choose',
        }])
        models.execute_kw(db, uid, password, 'base.language.export', 'act_getfile', [[export_id]])
        data = models.execute_kw(db, uid, password, 'base.language.export', 'read', [[export_id], ['data'], {'bin_size': False}])

        # content = data[0]['data'].data.decode('base64')
        content = data[0]['data']
        content = base64.b64decode(content)

        # xmlrpc_data = data[0]['data']
        # if isinstance(xmlrpc_data, xmlrpclib.Binary):
        #     content = xmlrpc_data.decode('utf-8')
        # else:
        #     content = xmlrpc_data.decode('base64')
        if m_name == 'base':
            for base_path in BASE_MODULE_PATH:
                if os.path.exists(base_path):
                    pot_path = base_path
                    break
        else:
            pot_path = os.path.join(addons_path, m_name, 'i18n')
        if not os.path.exists(pot_path):
            os.mkdir(pot_path)
        filepath = os.path.join(pot_path, m_name+'.pot')

        with open(filepath, 'wb') as f:
            f.write(content)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', required=True,
                        help='the name of the database to use')
    parser.add_argument('-l', '--login', default='admin',
                        help='user account, default \'admin\'')
    parser.add_argument('-p', '--password',
                        help='password of the user, default \'admin\', using prompt if login but no user is specified')
    parser.add_argument('--port', default=8069,
                        help='port to access the server, default \'8069\'')
    parser.add_argument('-m', '--modules',
                        help='the list of modules to install and export, comma separated')
    parser.add_argument('-P', '--project',
                        help='export Transifex configuration file for the following project')
    parser.add_argument('-i', '--install', action='store_true',
                        help='install modules before exporting')
    parser.add_argument('--no-export', action='store_true',
                        help='do not export translations')
    parser.add_argument('--include-be', action='store_true',
                        help='include l10n_be translations')

    args = parser.parse_args()

    port = args.port
    url = '%s://%s:%s' % ('http' if port != 443 else 'https', host, port)  # for local instance
    # url = '%s://%s' % ('http' if port != 443 else 'https', host)  # for saas instance
    
    if args.login == 'admin' and not args.password:
        args.password = 'admin'
    if not args.password:
        args.password = getpass.getpass(f"Password for user {args.login}: ")

    if args.modules == 'community':
        modules = ADDONS_1
    elif args.modules == 'l10n':
        modules = ADDONS_2
    elif args.modules == 'enterprise':
        modules = ENT_ADDONS_1
    elif args.modules == 'l10n_ent':
        modules = ENT_ADDONS_2
    # elif args.modules == 'l10n_be_hr_payroll':
    #     modules = ENT_ADDONS_BE_PAYROLL
    elif args.modules == 'theme':
        modules = THEME_ADDONS_1
    else:
        modules = (args.modules or '').split(',')

    modules_per_path = [(list(set(listed_modules) & set(modules)), p, tp)
                        for listed_modules, p, tp in [
                            (ADDONS_1, ADDONS_PATH, TXPATH),
                            (ENT_ADDONS_1, ENT_ADDONS_PATH, ENT_TXPATH),
                            (ADDONS_2, ADDONS_PATH, TXPATH),
                            (ENT_ADDONS_2, ENT_ADDONS_PATH, ENT_TXPATH),
                            # (ENT_ADDONS_BE_PAYROLL, ENT_ADDONS_PATH, ENT_TXPATH),
                            (THEME_ADDONS_1, THEME_PATH, THEME_TXPATH),
                            ]

                       ]

    for modules_list, addons_path, txpath in modules_per_path:
        if not modules_list:
            continue

        if not args.include_be:
            modules_list = [m for m in modules_list if 'l10n_be' not in m]

        if args.modules in ['theme']:
            for module in modules_list:
                if args.install:
                    install_modules([module], args.database, args.login, args.password, uninstall_incompatible=True)
                if not args.no_export:
                    export_terms([module], addons_path, args.database, args.login, args.password)
        else:
            if args.install:
                install_modules(modules_list, args.database, args.login, args.password)
            if not args.no_export:
                export_terms(modules_list, addons_path, args.database, args.login, args.password)

        if args.project:
            generate_tx_config(addons_path, txpath, args.project, modules_list)
