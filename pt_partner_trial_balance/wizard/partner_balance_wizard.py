# -*- coding: utf-8 -*-
# para ti.co sas Core ACCOUNTING MODULES
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Partner trial balance wizard
# models/partner_balance_wizard.py
from odoo import models, fields, api
import base64
import io
import xlsxwriter


class PartnerBalanceWizard(models.TransientModel):
    _name = 'partner.balance.wizard'
    _description = 'Partner Balance Wizard'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    partner_ids = fields.Many2many('res.partner', string='Partners')
    account_ids = fields.Many2many('account.account', string='Accounts')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def _prepare_query_conditions(self):
        conditions = [
            "aml.date < %s",
            "aml.company_id = %s"
        ]
        params = [self.start_date, self.company_id.id]

        if self.partner_ids:
            conditions.append("aml.partner_id = ANY(%s)")
            params.append(self.partner_ids.ids)
        if self.account_ids:
            conditions.append("aml.account_id = ANY(%s)")
            params.append(self.account_ids.ids)

        return " AND ".join(conditions), params

    def _prepare_transactions_conditions(self):
        conditions = [
            "aml.date BETWEEN %s AND %s",
            "aml.company_id = %s"
        ]
        params = [self.start_date, self.end_date, self.company_id.id]

        if self.partner_ids:
            conditions.append("aml.partner_id = ANY(%s)")
            params.append(self.partner_ids.ids)
        if self.account_ids:
            conditions.append("aml.account_id = ANY(%s)")
            params.append(self.account_ids.ids)

        return " AND ".join(conditions), params

    def generate_report(self):
        self.ensure_one()
        initial_conditions, initial_params = self._prepare_query_conditions()
        transactions_conditions, transactions_params = self._prepare_transactions_conditions()

        query = f"""
                            WITH initial_balances AS (
                                SELECT
                                    aml.partner_id,
                                    COALESCE(p.name, 'No Partner') AS partner_name,
                                    p.vat AS partner_vat,
                                    aml.account_id,
                                    a.name AS account_name,
                                    a.code AS account_code,
                                    SUM(aml.debit - aml.credit) AS initial_balance
                                FROM
                                    account_move_line aml
                                LEFT JOIN
                                    res_partner p ON aml.partner_id = p.id
                                JOIN
                                    account_account a ON aml.account_id = a.id
                                WHERE
                                    aml.parent_state = 'posted'
                                    {initial_conditions}
                                GROUP BY
                                    aml.partner_id, p.name, p.vat, aml.account_id, a.name, a.code
                            ),
                            transactions AS (
                                SELECT
                                    aml.partner_id,
                                    COALESCE(p.name, 'No Partner') AS partner_name,
                                    p.vat AS partner_vat,
                                    aml.account_id,
                                    a.name AS account_name,
                                    a.code AS account_code,
                                    SUM(aml.debit) AS sum_debits,
                                    SUM(aml.credit) AS sum_credits
                                FROM
                                    account_move_line aml
                                LEFT JOIN
                                    res_partner p ON aml.partner_id = p.id
                                JOIN
                                    account_account a ON aml.account_id = a.id
                                WHERE
                                    aml.parent_state = 'posted'
                                    {transactions_conditions}
                                GROUP BY
                                    aml.partner_id, p.name, p.vat, aml.account_id, a.name, a.code
                            )
                            SELECT
                                COALESCE(t.partner_id, i.partner_id) AS partner_id,
                                COALESCE(t.partner_name, i.partner_name) AS partner_name,
                                COALESCE(t.partner_vat, i.partner_vat) AS partner_vat,
                                COALESCE(t.account_id, i.account_id) AS account_id,
                                COALESCE(t.account_name, i.account_name) AS account_name,
                                COALESCE(t.account_code, i.account_code) AS account_code,
                                COALESCE(i.initial_balance, 0) AS initial_balance,
                                COALESCE(t.sum_debits, 0) AS sum_debits,
                                COALESCE(t.sum_credits, 0) AS sum_credits,
                                COALESCE(i.initial_balance, 0) + COALESCE(t.sum_debits, 0) - COALESCE(t.sum_credits, 0) AS ending_balance
                            FROM
                                initial_balances i
                            FULL OUTER JOIN
                                transactions t ON i.partner_id = t.partner_id AND i.account_id = t.account_id
                            ORDER BY
                                partner_name, account_name;
                        """
        params = initial_params + transactions_params
        self.env.cr.execute(query, params)
        results = self.env.cr.dictfetchall()

        report_obj = self.env['partner.balance.report']
        report_obj.search([]).unlink()  # Clear previous report data

        for result in results:
            report_obj.create(result)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Partner Balance Report',
            'view_mode': 'tree',
            'res_model': 'partner.balance.report',
            'target': 'current',
        }


class PartnerBalanceReport(models.TransientModel):
    _name = 'partner.balance.report'
    _description = 'Partner Balance Report'

    partner_id = fields.Many2one('res.partner', string='Partner')
    partner_name = fields.Char(string='Partner Name')
    partner_vat = fields.Char(string='Partner VAT')
    account_id = fields.Many2one('account.account', string='Account')
    account_code = fields.Char(string='Account Code')
    account_name = fields.Char(string='Account Name')
    initial_balance = fields.Float(string='Initial Balance')
    sum_debits = fields.Float(string='Sum of Debits')
    sum_credits = fields.Float(string='Sum of Credits')
    ending_balance = fields.Float(string='Ending Balance')

    def export_to_excel(self):
        records = self.search([])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Partner Balance')

        headers = ['Partner Name', 'Account Name', 'Initial Balance', 'Sum of Debits', 'Sum of Credits', 'Ending Balance']
        for col, header in enumerate(headers):
            sheet.write(0, col, header)

        for row, data in enumerate(records, start=1):
            sheet.write(row, 0, data.partner_name)
            sheet.write(row, 1, data.account_name)
            sheet.write(row, 2, data.initial_balance)
            sheet.write(row, 3, data.sum_debits)
            sheet.write(row, 4, data.sum_credits)
            sheet.write(row, 5, data.ending_balance)

        workbook.close()
        output.seek(0)

        export_id = self.env['ir.attachment'].create({
            'name': 'partner_balance_report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'store_fname': 'partner_balance_report.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        output.close()

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % export_id.id,
            'target': 'new',
        }
