# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def js_assign_outstanding_line(self, line_id):
        ''' Called by the 'payment' widget to reconcile a suggested journal item to the present
        invoice.

        :param line_id: The id of the line to reconcile with the current invoice.
        '''

        reg_line = self.env["account.move.line"].browse(line_id)
        if reg_line.account_id.id == self.partner_id.sale_advance_account_id.id:
            # create and account move to transfer the advance to the right account
            amount_residual = self.amount_residual
            if amount_residual <= reg_line.credit:
                amount = amount_residual
            else:
                amount = reg_line.credit

            move_vals = {
                'journal_id': reg_line.journal_id.id,
                'date': fields.Date.today(),
                'line_ids': [
                    (0, 0, {
                        'name': _('Descuento de Annticipo'),
                        'account_id': reg_line.account_id.id,
                        'debit': amount,
                        'credit': 0,
                    }),
                    (0, 0, {
                        'name': _('Descuento de Annticipo'),
                        'account_id': self.partner_id.property_account_receivable_id.id,
                        'debit': 0,
                        'credit': amount,
                    }),
                ],
            }
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            Nline_id = move.line_ids.filtered(lambda line: line.account_id == self.partner_id.property_account_receivable_id and not line.reconciled)
            aline_id = move.line_ids.filtered(
                lambda line: line.account_id == self.partner_id.sale_advance_account_id and not line.reconciled)
            line_id = Nline_id.id
            # reconcile reg_line with aline_id
            records = self.env['account.move.line'].browse([reg_line.id, aline_id.id])
            records.reconcile()

        elif reg_line.account_id.id == self.partner_id.purchase_advance_account_id.id:
            # create and account move to transfer the advance to the right account
            amount_residual = self.amount_residual
            if amount_residual <= reg_line.debit:
                amount = amount_residual
            else:
                amount = reg_line.debit
            move_vals = {
                'journal_id': reg_line.journal_id.id,
                'date': fields.Date.today(),
                'line_ids': [
                    (0, 0, {
                        'name': _('Descuento de Anticipo'),
                        'account_id': reg_line.account_id.id,
                        'debit': 0,
                        'credit': amount,
                    }),
                    (0, 0, {
                        'name': _('Descuento de Anticipo'),
                        'account_id': self.partner_id.property_account_payable_id.id,
                        'debit': amount,
                        'credit': 0,
                    }),
                ],
            }
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            Nline_id = move.line_ids.filtered(lambda line: line.account_id == self.partner_id.property_account_payable_id and not line.reconciled)
            line_id = Nline_id.id
            aline_id = move.line_ids.filtered(
                lambda line: line.account_id == self.partner_id.purchase_advance_account_id and not line.reconciled)
            # get reg_line and aline_id in a recordset
            records = self.env['account.move.line'].browse([reg_line.id, aline_id.id])
            records.reconcile()

        return super(AccountMove, self).js_assign_outstanding_line(line_id)

    def _compute_payments_widget_to_reconcile_info(self):
        for move in self:
            move.invoice_outstanding_credits_debits_widget = False
            move.invoice_has_outstanding = False

            if move.state != 'posted' \
                    or move.payment_state not in ('not_paid', 'partial') \
                    or not move.is_invoice(include_receipts=True):
                continue

            pay_term_lines = move.line_ids\
                .filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))

            if move.is_inbound():
                advanceaccount = move.partner_id.sale_advance_account_id.id
            else:
                advanceaccount = move.partner_id.purchase_advance_account_id.id

            domain = [
                '|',
                ('account_id', 'in', pay_term_lines.account_id.ids),
                ('account_id', '=', advanceaccount),
                ('parent_state', '=', 'posted'),
                ('partner_id', '=', move.commercial_partner_id.id),
                ('reconciled', '=', False),
                '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
            ]

            payments_widget_vals = {'outstanding': True, 'content': [], 'move_id': move.id}

            if move.is_inbound():
                domain.append(('balance', '<', 0.0))
                payments_widget_vals['title'] = _('Outstanding credits')
            else:
                domain.append(('balance', '>', 0.0))
                payments_widget_vals['title'] = _('Outstanding debits')

            for line in self.env['account.move.line'].search(domain):

                if line.currency_id == move.currency_id:
                    # Same foreign currency.
                    amount = abs(line.amount_residual_currency)
                else:
                    # Different foreign currencies.
                    amount = line.company_currency_id._convert(
                        abs(line.amount_residual),
                        move.currency_id,
                        move.company_id,
                        line.date,
                    )

                if move.currency_id.is_zero(amount):
                    continue

                payments_widget_vals['content'].append({
                    'journal_name': line.ref or line.move_id.name,
                    'amount': amount,
                    'currency_id': move.currency_id.id,
                    'id': line.id,
                    'move_id': line.move_id.id,
                    'date': fields.Date.to_string(line.date),
                    'account_payment_id': line.payment_id.id,
                })

            if not payments_widget_vals['content']:
                continue

            move.invoice_outstanding_credits_debits_widget = payments_widget_vals
            move.invoice_has_outstanding = True