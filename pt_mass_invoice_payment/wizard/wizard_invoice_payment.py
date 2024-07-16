# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class WizardInvoicePayment(models.TransientModel):
    _name = 'wizard.invoice.payment'
    _description = 'Invoice Payment Wizard'

    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True)
    rebate_journal_id = fields.Many2one('account.journal', string='Rebate Journal', required=True)
    rebate_account_id = fields.Many2one('account.account', string='Rebate Account', required=True)
    invoice_ids = fields.One2many('wizard.invoice.payment.line', 'wizard_id', string='Invoices')

    @api.model
    def default_get(self, fields):
        res = super(WizardInvoicePayment, self).default_get(fields)
        invoice_ids = self.env.context.get('active_ids')
        invoices = self.env['account.move'].browse(invoice_ids)
        lines = []
        for inv in invoices:
            lines.append((0, 0, {
                'invoice_id': inv.id,
                'customer_id': inv.partner_id.id,
                'date_invoice': inv.invoice_date,
                'date_due': inv.invoice_date_due,
                'amount_residual': inv.amount_residual,
                'amount_to_pay': inv.amount_residual,
                'full_pay': True,
            }))
        res.update({'invoice_ids': lines})
        return res

    def process_payments(self):
        if not self.invoice_ids:
            raise UserError('No invoices selected for payment processing.')

        first_invoice = self.invoice_ids[0].invoice_id
        invoice_type = first_invoice.move_type

        if invoice_type == 'out_invoice':
            self._process_invoice_payments()
        elif invoice_type == 'in_invoice':
            self._process_bill_payments()
        else:
            raise UserError('Unsupported invoice type: %s' % invoice_type)

    def _process_invoice_payments(self):
        """Logic to process customer invoices (out_invoice)"""

        invoices_by_partner = {}
        for line in self.invoice_ids:
            partner = line.customer_id
            account = line.invoice_id.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')).account_id.id
            if (partner.id, account) not in invoices_by_partner:
                invoices_by_partner[(partner.id, account)] = []
            invoices_by_partner[(partner.id, account)].append(line)

        for (partner, account), lines in invoices_by_partner.items():
            payment_vals = {
                'partner_id': partner,
                'amount': sum(line.amount_to_pay for line in lines),
                'currency_id': self.journal_id.currency_id.id or self.env.company.currency_id.id,
                'destination_account_id': account,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'journal_id': self.journal_id.id,
                'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                'date': fields.Date.today(),
            }
            payment = self.env['account.payment'].create(payment_vals)
            payment.action_post()

            for line in lines:
                self._reconcile_payment(line, payment)

    def _reconcile_payment(self, line, payment):
        move_lines = line.invoice_id.line_ids | payment.line_ids
        move_lines = move_lines.filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))

        amount_residual = line.invoice_id.amount_residual
        amount_to_pay = line.amount_to_pay

        if line.full_pay and amount_to_pay < amount_residual:
            diff_amount = amount_residual - amount_to_pay
            print('diff_amount', diff_amount)
            move_vals = {
                'name': '/',
                'ref': line.invoice_id.name,
                'journal_id': self.rebate_journal_id.id,
                'date': fields.Date.today(),
                'move_type': 'entry',
                'line_ids': [
                    (0, 0, {
                        'name': line.invoice_id.name,
                        'account_id': self.rebate_account_id.id,
                        'debit': diff_amount if diff_amount > 0 else 0.0,
                        'credit': 0.0 if diff_amount > 0 else -diff_amount,
                        'partner_id': line.customer_id.id,
                    }),
                    (0, 0, {
                        'name': line.invoice_id.name,
                        'account_id': line.invoice_id.line_ids.filtered(
                            lambda l: l.account_id.account_type == 'asset_receivable').account_id.id,
                        'credit': diff_amount if diff_amount > 0 else 0.0,
                        'debit': 0.0 if diff_amount > 0 else -diff_amount,
                        'partner_id': line.customer_id.id,
                    }),
                ],
            }
            account_move = self.env['account.move'].create(move_vals)
            account_move.action_post()
            move_lines |= account_move.line_ids

        move_lines = move_lines.filtered(
            lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))
        move_lines.reconcile()

    def _process_bill_payments(self):
        """Logic to process supplier bills (in_invoice)"""
        bills_by_partner = {}
        for line in self.invoice_ids:
            partner = line.customer_id
            account = line.invoice_id.line_ids.filtered(
                lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')).account_id.id
            if (partner.id, account) not in bills_by_partner:
                print('partner', partner.id)
                print('account', account)
                bills_by_partner[(partner.id, account)] = []
            bills_by_partner[(partner.id, account)].append(line)

        for (partner, account), lines in bills_by_partner.items():
            print('a partner', partner)
            print('a account', account)
            payment_vals = {
                'partner_id': partner,
                'amount': sum(line.amount_to_pay for line in lines),
                'currency_id': self.journal_id.currency_id.id or self.env.company.currency_id.id,
                'destination_account_id': account,
                'payment_type': 'outbound',
                'partner_type': 'supplier',
                'journal_id': self.journal_id.id,
                'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
                'date': fields.Date.today(),
            }
            payment = self.env['account.payment'].create(payment_vals)
            payment.action_post()
            print('payment', payment)

            for line in lines:
                self._reconcile_bill_payment(line, payment)

    def _reconcile_bill_payment(self, line, payment):
        move_lines = line.invoice_id.line_ids | payment.line_ids
        move_lines = move_lines.filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))

        amount_residual = line.invoice_id.amount_residual
        amount_to_pay = line.amount_to_pay

        if line.full_pay:
            if amount_to_pay < amount_residual:
                diff_amount = amount_residual - amount_to_pay

                move_vals = {
                    'name': '/',
                    'ref': line.invoice_id.name,
                    'journal_id': self.rebate_journal_id.id,
                    'move_type': 'entry',
                    'date': fields.Date.today(),
                    'line_ids': [
                        (0, 0, {
                            'name': line.invoice_id.name,
                            'account_id': self.rebate_account_id.id,
                            'debit': 0.0,
                            'credit': diff_amount,
                            'partner_id': line.customer_id.id,
                        }),
                        (0, 0, {
                            'name': line.invoice_id.name,
                            'account_id': line.invoice_id.line_ids.filtered(
                                lambda l: l.account_id.account_type == 'liability_payable').account_id.id,
                            'debit': diff_amount,
                            'credit': 0.0,
                            'partner_id': line.customer_id.id,
                        }),
                    ],
                }
                account_move = self.env['account.move'].create(move_vals)
                account_move.action_post()
                move_lines |= account_move.line_ids
            elif amount_to_pay == amount_residual:
                # No additional entries needed, just reconcile
                pass
        move_lines = move_lines.filtered(
            lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))
        move_lines.reconcile()


class WizardInvoicePaymentLine(models.TransientModel):
    _name = 'wizard.invoice.payment.line'
    _description = 'Invoice Payment Wizard Line'

    wizard_id = fields.Many2one('wizard.invoice.payment', string='Wizard', required=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', required=True)
    customer_id = fields.Many2one('res.partner', string='Customer', related='invoice_id.partner_id')
    date_invoice = fields.Date(string='Invoice Date', related='invoice_id.invoice_date')
    date_due = fields.Date(string='Due Date', related='invoice_id.invoice_date_due')
    amount_residual = fields.Monetary(string='Amount Residual', related='invoice_id.amount_residual')
    amount_to_pay = fields.Monetary(string='Amount to Pay')
    full_pay = fields.Boolean(string='Full Payment', default=True)
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id')
