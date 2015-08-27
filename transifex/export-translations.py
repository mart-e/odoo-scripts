#!/usr/bin/env python2
#
# export the terms of all odoo modules
#

import xmlrpclib
import os
import glob

host = 'localhost'
port = 8069
db = 'm1'

username = 'admin'
password = 'admin'

BASE_MODULE_PATH = '/home/mat/odoo/odoo/openerp/addons/base/i18n'
ADDONS_PATH = '/home/mat/odoo/odoo/addons/'
TXPATH = '/home/mat/odoo/odoo/.tx/config'
ENT_ADDONS_PATH = '/home/mat/odoo/enterprise/'
ENT_TXPATH = '/home/mat/odoo/enterprise/.tx/config'


l = glob.glob(os.path.join(ADDONS_PATH, '*/__init__.py'))
# without 'web' as is in enterprise and breaks if more than one 'theme_'
ADDONS_1 = [os.path.basename(os.path.dirname(i)) for i in l if ('l10n_' not in i and 'theme_' not in i and i != 'web')]
ADDONS_2 = [os.path.basename(os.path.dirname(i)) for i in l if ('l10n_' in i and 'l10n_be' not in i and 'l10n_ch' not in i and 'l10n_multilang' not in i)]
ADDONS_3 = [os.path.basename(os.path.dirname(i)) for i in l if ('l10n_be' in i or 'l10n_ch' in i or 'l10n_multilang' in i)]
# ADDONS_1 = ['account_cancel', 'rating', 'website_event', 'base_iban', 'account_voucher', 'analytic_contract_hr_expense', 'hr_equipment', 'website_mass_mailing', 'website_issue', 'crm_project_issue', 'web_analytics', 'website_gengo', 'purchase_requisition', 'web_tip', 'pos_reprint', 'analytic', 'website_sale', 'hw_escpos', 'board', 'website_sale_delivery', 'mail', 'sale_service', 'marketing_campaign', 'sale_stock', 'product_extended', 'hw_scale', 'payment_adyen', 'payment_transfer', 'base_import', 'mrp_byproduct', 'auth_oauth', 'web_view_editor', 'crm_partner_assign', 'mrp_repair', 'lunch', 'account_budget', 'report', 'resource', 'hr_payroll_account', 'sale_order_dates', 'website_mail', 'product_margin', 'inter_company_rules', 'survey_crm', 'stock_dropshipping', 'hw_proxy', 'hr_recruitment', 'project_issue_sheet', 'pos_mercury', 'auth_ldap', 'sale_crm', 'account_analytic_plans', 'sale_layout', 'crm', 'stock_picking_wave', 'hr_timesheet_invoice', 'website_quote', 'fetchmail', 'project_timesheet', 'mass_mailing', 'gamification', 'point_of_sale', 'base_import_module', 'website_event_track', 'calendar', 'google_account', 'event', 'sale_contract', 'website_version', 'website_slides', 'base_action_rule', 'web_editor', 'website_forum_doc', 'gamification_sale_crm', 'im_livechat', 'portal_sale', 'hw_scanner', 'account_test', 'account_analytic_default', 'marketing', 'link_tracker', 'analytic_user_function', 'hr_expense', 'web_gantt', 'fleet', 'website_hr', 'decimal_precision', 'payment_sips', 'purchase_analytic_plans', 'google_spreadsheet', 'portal_gamification', 'account_tax_python', 'website_sale_digital', 'stock_invoice_directly', 'survey', 'website_portal_sale', 'website_crm', 'website_portal', 'rating_project', 'procurement_jit', 'account_bank_statement_import', 'sale_mrp', 'website_twitter', 'website_links', 'google_calendar', 'website_livechat', 'marketing_campaign_crm_demo', 'website_customer', 'sale_analytic_plans', 'website_form', 'product_expiry', 'website_rating_project_issue', 'website_crm_score', 'website_google_map', 'barcodes', 'website_crm_claim', 'base_geolocalize', 'auth_crypt', 'payment_authorize', 'note_pad', 'website_membership', 'event_sale', 'payment_buckaroo', 'pos_discount', 'hr', 'bus', 'hr_timesheet', 'report_intrastat', 'delivery', 'web_kanban_gauge', 'anonymization', 'product_email_template', 'website_project_issue_sheet', 'subscription', 'website_forum', 'im_odoo_support', 'account', 'web_diagram', 'hw_posbox_homepage', 'account_check_printing', 'base_vat', 'rating_project_issue', 'web_kanban', 'utm', 'project', 'hr_holidays', 'hr_gamification', 'auth_signup', 'website_sale_options', 'website_event_sale', 'website', 'hr_contract', 'sale_journal', 'mrp_operations', 'payment_paypal', 'account_asset', 'warning', 'base_gengo', 'claim_from_delivery', 'crm_claim', 'stock_landed_costs', 'association', 'account_accountant', 'hr_payroll', 'website_crm_partner_assign', 'base_setup', 'hr_timesheet_sheet', 'product_visible_discount', 'hw_posbox_upgrade', 'website_project_issue', 'website_hr_recruitment', 'pos_restaurant', 'note', 'pos_loyalty', 'pad', 'website_blog', 'report_webkit', 'purchase_double_validation', 'document', 'sale_margin', 'stock', 'portal_stock', 'product', 'website_payment', 'im_chat', 'hr_attendance', 'project_issue', 'payment_ogone', 'web_calendar', 'membership', 'portal', 'stock_calendar', 'website_event_questions', 'payment', 'mail_tip', 'purchase', 'website_sale_stock', 'web_planner', 'website_partner', 'mrp', 'sale', 'pad_project', 'website_mail_channel', 'procurement', 'google_drive', 'sales_team', 'stock_account']
# ADDONS_2 = ['l10n_ae', 'l10n_lu', 'l10n_in', 'l10n_hu', 'l10n_ma', 'l10n_de_skr03', 'l10n_mx', 'l10n_sg', 'l10n_si', 'l10n_at', 'l10n_es', 'l10n_ca', 'l10n_et', 'l10n_cl', 'l10n_cn', 'l10n_co', 'l10n_th', 'l10n_ec', 'l10n_fr_hr_payroll', 'l10n_cr', 'l10n_tr', 'l10n_gr', 'l10n_ar', 'l10n_pt', 'l10n_syscohada', 'l10n_no', 'l10n_nl', 'l10n_pa', 'l10n_pe', 'l10n_vn', 'l10n_generic_coa', 'l10n_ro', 'l10n_pl', 'l10n_ve', 'l10n_de_skr04', 'l10n_eu_service', 'l10n_bo', 'l10n_uk', 'l10n_hr', 'l10n_in_hr_payroll', 'l10n_it', 'l10n_jp', 'l10n_de', 'l10n_us', 'l10n_br', 'l10n_hn', 'l10n_fr', 'l10n_do', 'l10n_uy', 'l10n_gt']
# ADDONS_3 = ['l10n_be', 'l10n_ch', 'l10n_be_hr_payroll_account', 'l10n_be_invoice_bba', 'l10n_be_hr_payroll', 'l10n_multilang', 'l10n_be_intrastat']


l = glob.glob(os.path.join(ENT_ADDONS_PATH, '*/__init__.py'))
ENT_ADDONS_1 = [os.path.basename(os.path.dirname(i)) for i in l if ('l10n_' not in i and 'theme_' not in i and i != 'website_portal_followup')]
ENT_ADDONS_2 = [os.path.basename(os.path.dirname(i)) for i in l if ('l10n_' in i and 'l10n_be' not in i and 'l10n_ch' not in i and 'l10n_multilang' not in i)]
ENT_ADDONS_3 = [os.path.basename(os.path.dirname(i)) for i in l if ('l10n_be' in i or 'l10n_ch' in i or 'l10n_multilang' in i)]
# ENT_ADDONS_1 = ['print_sale', 'sale_contract_asset', 'account_bank_statement_import_qif', 'account_sepa', 'account_batch_deposit', 'account_reports', 'delivery_fedex', 'account_plaid', 'project_timesheet_synchro', 'web', 'account_online_synch', 'print_docsaway', 'print', 'account_bank_statement_import_ofx', 'website_contract', 'account_extension', 'account_deferred_revenue', 'website_enterprise', 'website_form_editor', 'hr_appraisal', 'website_sign', 'account_contract_dashboard', 'account_reports_followup', 'sale_ebay']
# ENT_ADDONS_2 = ['l10n_us_check_printing']
# ENT_ADDONS_3 = ['l10n_be_reports', 'l10n_be_coda']

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

# generate_tx_config(ADDONS_PATH, TXPATH)
# generate_tx_config(ENT_ADDONS_PATH, ENT_TXPATH)

for i, modules_list in enumerate([ADDONS_1, ENT_ADDONS_1, ADDONS_2, ENT_ADDONS_2, ADDONS_3, ENT_ADDONS_3]):
    path = i % 2 and ENT_ADDONS_PATH or ADDONS_PATH
    install_modules(modules_list)
    export_terms(modules_list, path)
