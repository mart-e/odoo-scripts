#!/usr/bin/env python2
#
# install and export the terms of all odoo modules
#

import xmlrpclib
import os
import glob
from os.path import expanduser as e

# connection information
host = 'localhost'
port = 8069
db = '9e'

username = 'admin'
password = 'admin'

# paths to community and enterprise modules
BASE_MODULE_PATH = e('~/odoo/odoo/openerp/addons/base/i18n')
ADDONS_PATH = e('~/odoo/odoo/addons/')
TXPATH = e('~/odoo/odoo/.tx/config')
ENT_ADDONS_PATH = e('~/odoo/enterprise/')
ENT_TXPATH = e('~/odoo/enterprise/.tx/config')

l = glob.glob(os.path.join(ADDONS_PATH, '*/__init__.py'))
# without 'web' as is in enterprise and breaks if more than one 'theme_'
ADDONS_1 = [os.path.basename(os.path.dirname(i)) for i in l if ('l10n_' not in i and 'theme_' not in i and os.path.basename(os.path.dirname(i)) != 'web')] + ['base']
ADDONS_2 = [os.path.basename(os.path.dirname(i)) for i in l if ('l10n_' in i and 'l10n_be' not in i and 'l10n_ch' not in i and 'l10n_multilang' not in i)]
ADDONS_3 = [os.path.basename(os.path.dirname(i)) for i in l if ('l10n_be' in i or 'l10n_ch' in i or 'l10n_sa' in i or 'l10n_multilang' in i)]

l = glob.glob(os.path.join(ENT_ADDONS_PATH, '*/__init__.py'))
ENT_ADDONS_1 = [os.path.basename(os.path.dirname(i)) for i in l if (
    'l10n_' not in i and
    'theme_' not in i and
    os.path.basename(os.path.dirname(i)) != 'website_portal_followup' and
    os.path.basename(os.path.dirname(i)) != 'account_extension')]
ENT_ADDONS_2 = [os.path.basename(os.path.dirname(i)) for i in l if ('l10n_' in i and 'l10n_be' not in i and 'l10n_ch' not in i and 'l10n_multilang' not in i)]
ENT_ADDONS_3 = [os.path.basename(os.path.dirname(i)) for i in l if ('l10n_be' in i or 'l10n_ch' in i or 'l10n_sa' in i or 'l10n_multilang' in i)]

# the list of lists of modules to export, alterning community and enterpruse modules
# e.g. MODULES_TO_EXPORT = [[], ['account_contract_dashboard', 'account_reports']]
MODULES_TO_EXPORT = [ADDONS_1, ENT_ADDONS_1, ADDONS_2, ENT_ADDONS_2, ADDONS_3, ENT_ADDONS_3]


uid = None
url = '%s://%s:%s' % ('http' if port != 443 else 'https', host, port)  # for local instance
# url = '%s://%s' % ('http' if port != 443 else 'https', host)  # for saas instance


def generate_tx_config(addons_path, tx_path):
    """ generate the .tx/config file based on list of addons

    WARNING if a .pot file is empty, the module should be removed manually from
    this file (otherwise tx client will complain)
    $ ls -lh addons/*/i18n/*.pot | grep 432
    """
    l = glob.glob(addons_path+'*/__init__.py')
    modules = list(set(os.path.basename(os.path.dirname(i)) for i in l))
    modules.sort()

    configf = open(tx_path, 'w')
    configf.write("""[main]
host = https://www.transifex.com
type = PO

""")

    prepath = ''
    if 'enterprise' not in addons_path:
        configf.write("""[odoo-9.base]
file_filter = openerp/addons/base/i18n/<lang>.po
source_file = openerp/addons/base/i18n/base.pot
source_lang = en

""")
        prepath = 'addons/'

    for m in modules:
        configf.write("""[odoo-9.%s]
file_filter = %s%s/i18n/<lang>.po
source_file = %s%s/i18n/%s.pot
source_lang = en

""" % (m, prepath, m, prepath, m, m))

    configf.close()


def install_modules(modules):
    common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    print "Logged in as %s (uid: %d)" % (username, uid)

    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    module_ids = models.execute_kw(db, uid, password, 'ir.module.module', 'search',  [[('name', 'in', modules)]])
    models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_install',  [module_ids])


def export_terms(modules, addons_path):
    """ generate all .pot files

    WARNING check release.py version info or can be corrected with
    $ sed -i 's/Odoo Server 9.0alpha1/Odoo Server 9.0/g' addons/*/i18n/*.pot

    could also be useful to remove "empty" changes
    $ git status --short | grep '.pot' | sed 's/^ M *//' | xargs -I {} bash -c 'if test `git diff {} | grep "^+" | grep -v "^+++\|^+#\|POT-Creation-Date\|PO-Revision-Date" | wc -l` -eq 0; then git checkout -- {}; fi'
    """

    common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    print "Logged in as %s (uid: %d)" % (username, uid)

    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    modules = models.execute_kw(db, uid, password, 'ir.module.module', 'search_read',  [
        [
            ('state', '=', 'installed'),
            ('name', 'in', modules),
        ],
        ['name']])

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
        content = data[0]['data'].decode('base64')
        if m_name == 'base':
            pot_path = BASE_MODULE_PATH
        else:
            pot_path = os.path.join(addons_path, m_name, 'i18n')
        if not os.path.exists(pot_path):
            os.mkdir(pot_path)
        filepath = os.path.join(pot_path, m_name+'.pot')
        with open(filepath, 'w') as f:
            f.write(content)

    # sed -i 's/Odoo Server 9.0alpha1/Odoo Server 9.0/g' **/i18n/*.pot
    # sed -i 's/Odoo Server 9.0rc1/Odoo Server 9.0/g' **/i18n/*.pot
    # git status --short | grep '.pot' | grep  -v "^??" | sed 's/^ M *//' | sed 's/^?? *//' | xargs -I {} bash -c 'if test `git diff {} | grep "^+\|^-" | grep -v "^+++\|^---\|^+#\|Last-Translator\|PO-Revision-Date\|POT-Creation-Date" | wc -l` -eq 0; then git checkout -- {}; fi'
    # git status --short | grep '.pot' | grep  -v "^??" | sed 's/^ M *//' | sed 's/^?? *//' | xargs -I {} bash -c 'if test `git diff {} | grep "^+msgid\|^-msgid" | wc -l` -eq 0; then git checkout -- {}; fi'
    # ls -lh **/i18n/*.pot | grep 432 | sed  "s/ /\\n/g" | grep ".pot" | xargs rm

# generate_tx_config(ADDONS_PATH, TXPATH)
# generate_tx_config(ENT_ADDONS_PATH, ENT_TXPATH)

for i, modules_list in enumerate(MODULES_TO_EXPORT):
    path = i % 2 and ENT_ADDONS_PATH or ADDONS_PATH
    install_modules(modules_list)
    export_terms(modules_list, path)
