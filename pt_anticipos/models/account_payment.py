# -*- coding: utf-8 -*-
# developed by Para ti.co SAS 2024 by Cesar Ortiz

from odoo import _, api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    isadvance = fields.Boolean(string="Is Advance", default=False)

    @api.depends('journal_id', 'partner_id', 'partner_type', 'is_internal_transfer', 'destination_journal_id','isadvance')
    def _compute_destination_account_id(self):
        super(AccountPayment, self)._compute_destination_account_id()

        if self.isadvance and not self.is_internal_transfer:
            self.destination_account_id = False
            for pay in self:
                if pay.partner_type == 'customer':
                    # Receive money from invoice or send money to refund it.
                    if pay.partner_id:
                        pay.destination_account_id = pay.partner_id.with_company(
                            pay.company_id).sale_advance_account_id
                    else:
                        pay.destination_account_id = self.env['account.account'].search([
                            ('company_id', '=', pay.company_id.id),
                            ('account_type', '=', 'asset_receivable'),
                            ('deprecated', '=', False),
                        ], limit=1)
                elif pay.partner_type == 'supplier':
                    # Send money to pay a bill or receive money to refund it.
                    if pay.partner_id:
                        pay.destination_account_id = pay.partner_id.with_company(pay.company_id).purchase_advance_account_id
                    else:
                        pay.destination_account_id = self.env['account.account'].search([
                            ('company_id', '=', pay.company_id.id),
                            ('account_type', '=', 'liability_payable'),
                            ('deprecated', '=', False),
                        ], limit=1)
