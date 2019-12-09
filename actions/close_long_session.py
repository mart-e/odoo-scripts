import time
from odoo.exceptions import UserError

self = self.sudo(1)
session = self.env['pos.session'].browse(68)
company_id = session.config_id.company_id.id
ctx = dict(self.env.context, force_company=company_id, company_id=company_id)
for st in session.statement_ids:
    statement = st.with_context(ctx).sudo()
    moves = self.env['account.move']
    for st_line in statement.line_ids:
        if st_line.account_id and not st_line.journal_entry_ids.ids:
            st_line.fast_counterpart_creation()
        elif not st_line.journal_entry_ids.ids and not statement.currency_id.is_zero(st_line.amount):
            raise UserError('All the account entries lines must be processed in order to close the statement.')
        for aml in st_line.journal_entry_ids:
            moves |= aml.move_id
    if moves:
        moves.filtered(lambda m: m.state != 'posted').post()
    statement.message_post(body='Statement %s confirmed, journal items were created.' % (statement.name,))

session.statement_ids.link_bank_to_partner()
session.statement_ids.write({'state': 'confirm', 'date_done': time.strftime("%Y-%m-%d %H:%M:%S")})
session.with_context(ctx)._confirm_orders()
session.write({'state': 'closed'})
self.env.cr.commit()
