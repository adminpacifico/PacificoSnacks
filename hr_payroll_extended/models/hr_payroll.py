# -*- coding: utf-8 -*-
from datetime import date, datetime, time, timedelta

import babel
from dateutil.relativedelta import relativedelta
from pytz import timezone

from odoo.tools import float_round, date_utils
from odoo.tools.misc import format_date
from odoo.tools.safe_eval import safe_eval

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, AccessError, ValidationError

import base64
from dateutil.relativedelta import relativedelta
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips
from odoo.exceptions import UserError, ValidationError


def days_between(start_date, end_date):
    #Add 1 day to end date to solve different last days of month 
    #s1, e1 =  datetime.strptime(start_date,"%Y-%m-%d") , datetime.strptime(end_date,"%Y-%m-%d")  + timedelta(days=1)
    s1, e1 =  start_date , end_date + timedelta(days=1)
    #Convert to 360 days
    s360 = (s1.year * 12 + s1.month) * 30 + s1.day
    e360 = (e1.year * 12 + e1.month) * 30 + e1.day
    #Count days between the two 360 dates and return tuple (months, days)
    res = divmod(e360 - s360, 30)
    return ((res[0] * 30) + res[1]) or 0

def days360(s, e):
    return ( ((e.year * 12 + e.month) * 30 + e.day) - ((s.year * 12 + s.month) * 30 + s.day))

           
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    type_payslip_id = fields.Many2one('hr.type.payslip', string="Type")

    def actualizar_entradas(self):
        res = self._onchange_employee()
        inputs = self.get_inputs(self.contract_id, self.date_from, self.date_to)
        return True

    def get_inputs_hora_extra(self, contract_id, date_from, date_to):
        self._cr.execute(''' SELECT i.name, i.code, h.total_money, i.id, h.hour_value, h.amount FROM hr_extras h
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approved'
                                AND h.date BETWEEN %s AND %s
                                ORDER BY i.code''',(contract_id.id, date_from, date_to))
        horas_extras = self._cr.fetchall()
        return horas_extras

    def get_inputs_hora_extra_month_before(self, contract_id, date_from, date_to):
        date_before = date_from - relativedelta(months=1)
        date_before_from = date(date_before.year, date_before.month, 1)
        date_before_to = date(date_from.year, date_from.month, 1) - relativedelta(days=1)

        self._cr.execute(''' SELECT i.name, i.code, h.total_money, i.id FROM hr_extras h
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approved'
                                AND h.date BETWEEN %s AND %s
                                ORDER BY i.code''',(contract_id.id, date_before_from, date_before_to))
        horas_extras = self._cr.fetchall()
        return horas_extras

    def get_inputs_hora_extra_12month_before(self, contract_id, date_from, date_to):
        hm12_date_ini = date_to - relativedelta(months=12)
        hm12_date_ini = hm12_date_ini + relativedelta(days=1)
        if contract_id.date_start <= hm12_date_ini:
            hm12_date_init = hm12_date_ini
        else:
            hm12_date_init = contract_id.date_start

        self._cr.execute(''' SELECT i.name, i.code, h.total_money, i.id FROM hr_extras h
                                   INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                   WHERE h.contract_id=%s AND h.state='approved'
                                   AND h.date BETWEEN %s AND %s
                                   ORDER BY i.code''', (contract_id.id, hm12_date_init, date_to))
        horas_extras = self._cr.fetchall()
        return horas_extras

    def get_inputs_hora_extra_year_now(self, contract_id, date_from, date_to):
        date_init_year = date(date_from.year, 1, 1)
        if contract_id.date_start <= date_init_year:
            date_init = date_init_year
        else:
            date_init = contract_id.date_start

        self._cr.execute(''' SELECT i.name, i.code, h.total_money, i.id FROM hr_extras h
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approved'
                                AND h.date BETWEEN %s AND %s
                                ORDER BY i.code''',(contract_id.id, date_init, date_to))
        horas_extras = self._cr.fetchall()
        return horas_extras

    def get_inputs_hora_extra_6month(self, contract_id, date_from, date_to):

        if date_from.month <= 6 and date_from.day <= 31:
            date_init_year = date(date_from.year, 1, 1)

        elif date_from.month <= 12 and date_from.day <= 31:
            date_init_year = date(date_from.year, 7, 1)

        if contract_id.date_start <= date_init_year:
            date_init = date_init_year
        else:
            date_init = contract_id.date_start

        self._cr.execute(''' SELECT i.name, i.code, h.total_money, i.id FROM hr_extras h
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approved'
                                AND h.date BETWEEN %s AND %s
                                ORDER BY i.code''',(contract_id.id, date_init, date_to))
        horas_extras = self._cr.fetchall()
        return horas_extras

    def get_inputs_loans(self, contract_id, date_from, date_to):
        self._cr.execute(''' SELECT i.name, i.code, l.amount, i.id
                                FROM hr_loan_line l
                                INNER JOIN hr_loan h ON h.id=l.loan_id
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approve'
                                AND l.date BETWEEN %s AND %s
                                AND h.loan_fijo IS False
                                ORDER BY i.code ''',(contract_id.id, date_from, date_to))
        loans_ids = self._cr.fetchall()
        return loans_ids

    def get_inputs_loans_month_before(self, contract_id, date_from, date_to):
        date_before = date_from - relativedelta(months=1)
        date_before_from = date(date_before.year, date_before.month, 1)
        date_before_to = date(date_from.year, date_from.month, 1) - relativedelta(days=1)

        self._cr.execute(''' SELECT i.name, i.code, l.amount, i.id
                                FROM hr_loan_line l
                                INNER JOIN hr_loan h ON h.id=l.loan_id
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approve'
                                AND l.date BETWEEN %s AND %s
                                AND h.loan_fijo IS False
                                ORDER BY i.code ''', (contract_id.id, date_before_from, date_before_to))
        loans_ids = self._cr.fetchall()
        return loans_ids

    def get_inputs_loans_month_now(self, contract_id, date_from, date_to):
        date_month_now_from = date(date_from.year, date_from.month, 1)
        date_month_next = date_month_now_from + relativedelta(months=1)
        date_month_now_to = date(date_month_next.year, date_month_next.month, 1) - relativedelta(days=1)

        self._cr.execute(''' SELECT i.name, i.code, l.amount, i.id
                                FROM hr_loan_line l
                                INNER JOIN hr_loan h ON h.id=l.loan_id
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approve'
                                AND l.date BETWEEN %s AND %s
                                AND h.loan_fijo IS False
                                ORDER BY i.code ''', (contract_id.id, date_month_now_from, date_month_now_to))
        loans_ids = self._cr.fetchall()
        return loans_ids

    def get_inputs_total_ingreso(self, contract_id, date_from, date_to):
        date_before_from = date(date_from.year, date_from.month, 1)
        date_before_to = date(date_from.year, date_from.month, 15)
        payslip = self.env['hr.payslip'].search([("contract_id", "=", contract_id.id),
                                                 ("date_from", "=", date_before_from),
                                                 ("date_to", "=", date_before_to),
                                                 ("type_payslip_id.name", "=", 'Nomina'),
                                                 ("state", "=", 'done')], limit=1)
        if payslip.id :
            total_ingreso = self.env['hr.payslip.line'].search([("code", "=", 'GROSS'),("slip_id.id", "=", payslip.id)], limit=1)
        else:
            total_ingreso = False
        return total_ingreso

    def get_inputs_aux_movilizacion(self, contract_id, date_from, date_to):
        date_before_from = date(date_from.year, date_from.month, 1)
        date_before_to = date(date_from.year, date_from.month, 15)
        payslip = self.env['hr.payslip'].search([("contract_id", "=", contract_id.id),
                                                 ("date_from", "=", date_before_from),
                                                 ("date_to", "=", date_before_to),
                                                 ("type_payslip_id.name", "=", 'Nomina'),
                                                 ("state", "=", 'done')], limit=1)
        if payslip.id :
            aux_movilizacion = self.env['hr.payslip.line'].search([("code", "=", 'AUX_MOVILIZACION'),("slip_id.id", "=", payslip.id)], limit=1)
        else:
            aux_movilizacion = False
        return aux_movilizacion

    def get_inputs_aux_rodamiento(self, contract_id, date_from, date_to):
        date_before_from = date(date_from.year, date_from.month, 1)
        date_before_to = date(date_from.year, date_from.month, 15)
        payslip = self.env['hr.payslip'].search([("contract_id", "=", contract_id.id),
                                                 ("date_from", "=", date_before_from),
                                                 ("date_to", "=", date_before_to),
                                                 ("type_payslip_id.name", "=", 'Nomina'),
                                                 ("state", "=", 'done')], limit=1)
        if payslip.id :
            aux_rodamiento = self.env['hr.payslip.line'].search([("code", "=", 'AUX_RODAMIENTO'),("slip_id.id", "=", payslip.id)], limit=1)
        else:
            aux_rodamiento = False
        return aux_rodamiento

    def get_inputs_loans_12month_before(self, contract_id, date_from, date_to):
        lm12_date_ini = date_to - relativedelta(months=12)
        lm12_date_ini = lm12_date_ini + relativedelta(days=1)
        if contract_id.date_start <= lm12_date_ini:
            lm12_date_init = lm12_date_ini
        else:
            lm12_date_init = contract_id.date_start

        self._cr.execute(''' SELECT i.name, i.code, l.amount, i.id
                                FROM hr_loan_line l
                                INNER JOIN hr_loan h ON h.id=l.loan_id
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approve'
                                AND l.date BETWEEN %s AND %s
                                AND h.loan_fijo IS False
                                ORDER BY i.code ''', (contract_id.id, lm12_date_init, date_to))
        loans_ids = self._cr.fetchall()
        return loans_ids

    def get_inputs_loans_year_now(self, contract_id, date_from, date_to):
        date_init_year = date(date_from.year, 1, 1)
        if contract_id.date_start <= date_init_year:
            date_init = date_init_year
        else:
            date_init = contract_id.date_start
        self._cr.execute(''' SELECT i.name, i.code, l.amount, i.id
                                FROM hr_loan_line l
                                INNER JOIN hr_loan h ON h.id=l.loan_id
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approve'
                                AND l.date BETWEEN %s AND %s
                                AND h.loan_fijo IS False
                                ORDER BY i.code ''', (contract_id.id, date_init, date_to))
        loans_ids = self._cr.fetchall()
        return loans_ids

    def get_inputs_loans_6month(self, contract_id, date_from, date_to):
        if date_from.month <= 6 and date_from.day <= 31:
            date_init_year = date(date_from.year, 1, 1)

        elif date_from.month <= 12 and date_from.day <= 31:
            date_init_year = date(date_from.year, 7, 1)

        if contract_id.date_start <= date_init_year:
            date_init = date_init_year
        else:
            date_init = contract_id.date_start
        self._cr.execute(''' SELECT i.name, i.code, l.amount, i.id
                                FROM hr_loan_line l
                                INNER JOIN hr_loan h ON h.id=l.loan_id
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approve'
                                AND l.date BETWEEN %s AND %s
                                AND h.loan_fijo IS False
                                ORDER BY i.code ''', (contract_id.id, date_init, date_to))
        loans_ids = self._cr.fetchall()
        return loans_ids



    def get_amount_transport_subsidy_year(self, contract_id, date_from, date_to):
        count = 0
        amount_transp = 0
        date_init_year = date(date_from.year, 1, 1)
        if contract_id.date_start <= date_init_year:
            date_init = date_init_year
        else:
            date_init = contract_id.date_start
        date_end = date(date_init.year, date_init.month, 1) + relativedelta(months=1)
        date_end = date_end - relativedelta(days=1)

        while date_end <= date_to:

            transport_subsidy_ids = self.env['hr.payroll_data'].search([("contract_id", "=", contract_id.id),
                                                                         ("fecha_final", ">=",date_init),
                                                                         ("fecha_final", "<=", date_end),
                                                                         ])
            if transport_subsidy_ids:
                for t in transport_subsidy_ids:
                    amount_transp += transport_subsidy_ids.auxilio_transporte
                count += 1
            else:
                payslip = self.env['hr.payslip'].search([("contract_id", "=", contract_id.id),
                                                                           ("date_from", ">=", date_init),
                                                                           ("date_to", "<=", date_end),
                                                                           ("type_payslip_id.name", "=", 'Nomina'),
                                                                            ], limit=1)
                if payslip:
                    for slip in payslip:
                        transport_subsidy_payslip = payslip.line_ids.search([("code", "=", 'SUBSTRAN'),("slip_id", "=", slip.id)], limit=1)
                        if transport_subsidy_payslip:
                            amount_transp += transport_subsidy_payslip.total
                            count += 1
                        else:
                            amount_transp += 0
                            count += 1

                else:
                    amount_transp += 0
                    count += 1

            date_init = date_init + relativedelta(months=1)
            date_end = date(date_init.year, date_init.month, 1) + relativedelta(months=1)
            date_end = date_end - relativedelta(days=1)

        if count == 0:
            amount_transp = amount_transp
        else:
            amount_transp = amount_transp / count

        return amount_transp

    def get_inputs_withholding_tax(self, contract_id, date_from, date_to):
        date_month_now_from = date(date_from.year, date_from.month, 1)
        date_month_next = date_month_now_from + relativedelta(months=1)
        date_month_now_to = date(date_month_next.year, date_month_next.month, 1) - relativedelta(days=1)
        withholding_tax_ids = self.env['hr.withholding.tax'].search([("contract_id", "=", contract_id.id),
                                                                     ("deductions_rt_id.date", ">=", date_month_now_from),
                                                                     ("deductions_rt_id.date", "<=", date_month_now_to),
                                                                     ("state", "=", 'approved'),
                                                                     ], limit=1)

        return withholding_tax_ids

    def get_inputs_exempt_income_tax(self, contract_id, date_from, date_to):
        date_month_now_from = date(date_from.year, date_from.month, 1)
        date_month_next = date_month_now_from + relativedelta(months=1)
        date_month_now_to = date(date_month_next.year, date_month_next.month, 1) - relativedelta(days=1)
        exempt_income_tax_ids = self.env['hr_exempt_income_tax'].search([("contract_id", "=", contract_id.id),
                                                                     ("exempt_income_id.date", ">=", date_month_now_from),
                                                                     ("exempt_income_id.date", "<=", date_month_now_to),
                                                                     ("state", "=", 'approved'),
                                                                     ], limit=1)

        return exempt_income_tax_ids

    def get_inputs_loans_fijos(self, contract_id):
        self._cr.execute(''' SELECT i.name, i.code, h.loan_amount
                                FROM hr_loan h
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approve'
                                AND h.loan_fijo IS True
                                ORDER BY i.code ''',(contract_id.id,))
        loans_fijos_ids = self._cr.fetchall()
        return loans_fijos_ids

    def get_suspensions_day(self, contract_id, date_from, date_to):
        suspensions = self.env['hr.leave'].search([('contract_id', '=', contract_id.id),('holiday_status_id.code', '=', 'SUSPENSION'),
                                                   ('state', '=', 'validate'), ("date_from", ">=", date_from), ("date_to", "<=", date_to)])
        suspension = 0
        for s in suspensions:
            suspension = suspension + s.workday

        return suspension

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = []

        self._cr.execute(''' DELETE FROM hr_payslip_input WHERE payslip_id=%s ''', (self.id,))
        for contract in contracts:

            # Horas Extras
            horas_extras = self.get_inputs_hora_extra(contract, date_from, date_to)
            if horas_extras:
                extradiurna_amount = 0
                extradiurnafestivo_amount = 0
                extranocturna_amount = 0
                extranocturnafestivo_amount = 0
                recargonocturno_amount = 0
                recargodiurnofestivo_amounth = 0
                recargonocturnofestivo_amount = 0
                for hora in horas_extras:
                    if hora[1] == 'EXTRADIURNA':
                        extradiurna_amount = extradiurna_amount + hora[2]
                        extradiurna_type_id = hora[3]
                        extradiurna_name = hora[0]
                        extradiurna_code = hora[1]
                    if hora[1] == 'EXTRADIURNAFESTIVO':
                        extradiurnafestivo_amount = extradiurnafestivo_amount + hora[2]
                        extradiurnafestivo_type_id = hora[3]
                        extradiurnafestivo_name = hora[0]
                        extradiurnafestivo_code = hora[1]
                    if hora[1] == 'EXTRANOCTURNA':
                        extranocturna_amount = extranocturna_amount + hora[2]
                        extranocturna_type_id = hora[3]
                        extranocturna_name = hora[0]
                        extranocturna_code = hora[1]
                    if hora[1] == 'EXTRANOCTURNAFESTIVO':
                        extranocturnafestivo_amount = extranocturnafestivo_amount + hora[2]
                        extranocturnafestivo_type_id = hora[3]
                        extranocturnafestivo_name = hora[0]
                        extranocturnafestivo_code = hora[1]
                    if hora[1] == 'RECARGONOCTURNO':
                        recargonocturno_amount = recargonocturno_amount + hora[2]
                        recargonocturno_type_id = hora[3]
                        recargonocturno_name = hora[0]
                        recargonocturno_code = hora[1]
                    if hora[1] == 'RECARGODIURNOFESTIVO':
                        recargodiurnofestivo_amounth = recargodiurnofestivo_amounth + hora[2]
                        recargodiurnofestivo_type_id = hora[3]
                        recargodiurnofestivo_name = hora[0]
                        recargodiurnofestivo_code = hora[1]
                    if hora[1] == 'RECARGONOCTURNOFESTIVO':
                        recargonocturnofestivo_amount = recargonocturnofestivo_amount + hora[2]
                        recargonocturnofestivo_type_id = hora[3]
                        recargonocturnofestivo_name = hora[0]
                        recargonocturnofestivo_code = hora[1]
                if not extradiurna_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": extradiurna_amount,
                        "payslip_id": self.id,
                        "input_type_id": extradiurna_type_id,
                        "name_input": extradiurna_name,
                        "code_input": extradiurna_code,
                    })
                if not extradiurnafestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": extradiurnafestivo_amount,
                        "payslip_id": self.id,
                        "input_type_id": extradiurnafestivo_type_id,
                        "name_input": extradiurnafestivo_name,
                        "code_input": extradiurnafestivo_code,
                    })
                if not extranocturna_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": extranocturna_amount,
                        "payslip_id": self.id,
                        "input_type_id": extranocturna_type_id,
                        "name_input": extranocturna_name,
                        "code_input": extranocturna_code,
                    })
                if not extranocturnafestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": extranocturnafestivo_amount,
                        "payslip_id": self.id,
                        "input_type_id": extranocturnafestivo_type_id,
                        "name_input": extranocturnafestivo_name,
                        "code_input": extranocturnafestivo_code,
                    })
                if not recargonocturno_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": recargonocturno_amount,
                        "payslip_id": self.id,
                        "input_type_id": recargonocturno_type_id,
                        "name_input": recargonocturno_name,
                        "code_input": recargonocturno_code,
                    })
                if not recargodiurnofestivo_amounth == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": recargodiurnofestivo_amounth,
                        "payslip_id": self.id,
                        "input_type_id": recargodiurnofestivo_type_id,
                        "name_input": recargodiurnofestivo_name,
                        "code_input": recargodiurnofestivo_code,
                    })
                if not recargonocturnofestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": recargonocturnofestivo_amount,
                        "payslip_id": self.id,
                        "input_type_id": recargonocturnofestivo_type_id,
                        "name_input": recargonocturnofestivo_name,
                        "code_input": recargonocturnofestivo_code,
                    })

            # Horas extras mes anterior
            hora_extra_month_before = self.get_inputs_hora_extra_month_before(contract, date_from, date_to)
            if hora_extra_month_before:
                extradiurna_amount_ant = 0
                extradiurnafestivo_amount_ant = 0
                extranocturna_amount_ant = 0
                extranocturnafestivo_amount_ant = 0
                recargonocturno_amount_ant = 0
                recargodiurnofestivo_amount_ant = 0
                recargonocturnofestivo_amount_ant = 0
                for hora in hora_extra_month_before:
                    if hora[1] == 'EXTRADIURNA':
                        extradiurna_amount_ant = extradiurna_amount_ant + hora[2]
                        extradiurna_type_id_ant = hora[3]
                    if hora[1] == 'EXTRADIURNAFESTIVO':
                        extradiurnafestivo_amount_ant = extradiurnafestivo_amount_ant + hora[2]
                        extradiurnafestivo_type_id_ant = hora[3]
                    if hora[1] == 'EXTRANOCTURNA':
                        extranocturna_amount_ant = extranocturna_amount_ant + hora[2]
                        extranocturna_type_id_ant = hora[3]
                    if hora[1] == 'EXTRANOCTURNAFESTIVO':
                        extranocturnafestivo_amount_ant = extranocturnafestivo_amount_ant + hora[2]
                        extranocturnafestivo_type_id_ant = hora[3]
                    if hora[1] == 'RECARGONOCTURNO':
                        recargonocturno_amount_ant = recargonocturno_amount_ant + hora[2]
                        recargonocturno_type_id_ant = hora[3]
                    if hora[1] == 'RECARGODIURNOFESTIVO':
                        recargodiurnofestivo_amount_ant = recargodiurnofestivo_amount_ant + hora[2]
                        recargodiurnofestivo_type_id_ant = hora[3]
                    if hora[1] == 'RECARGONOCTURNOFESTIVO':
                        recargonocturnofestivo_amount_ant = recargonocturnofestivo_amount_ant + hora[2]
                        recargonocturnofestivo_type_id_ant = hora[3]
                if not extradiurna_amount_ant == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": extradiurna_amount_ant,
                        "payslip_id": self.id,
                        "input_type_id": extradiurna_type_id_ant,
                        "code_input": 'EXTRADIURNA_ANT30',
                        "name_input": 'Horas Extra Diurna (25%) Mes Anterior',
                    })
                if not extradiurnafestivo_amount_ant == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": extradiurnafestivo_amount_ant,
                        "payslip_id": self.id,
                        "input_type_id": extradiurnafestivo_type_id_ant,
                        "code_input": 'EXTRADIURNAFESTIVO_ANT30',
                        "name_input": '	Horas Extra Diurna Festivo (100%) Mes Anterior',
                    })
                if not extranocturna_amount_ant == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": extranocturna_amount_ant,
                        "payslip_id": self.id,
                        "input_type_id": extranocturna_type_id_ant,
                        "code_input": 'EXTRANOCTURNA_ANT30',
                        "name_input": 'Horas Extra Nocturna (75%) Mes Anterior',
                    })
                if not extranocturnafestivo_amount_ant == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": extranocturnafestivo_amount_ant,
                        "payslip_id": self.id,
                        "input_type_id": extranocturnafestivo_type_id_ant,
                        "code_input": 'EXTRANOCTURNAFESTIVO_ANT30',
                        "name_input": 'Horas Extra Nocturna Festivo (150%) Mes Anterior',
                    })
                if not recargonocturno_amount_ant == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": recargonocturno_amount_ant,
                        "payslip_id": self.id,
                        "input_type_id": recargonocturno_type_id_ant,
                        "code_input": 'RECARGONOCTURNO_ANT30',
                        "name_input": 'Horas Recargo Nocturno (35%) Mes Anterior',
                    })
                if not recargodiurnofestivo_amount_ant == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": recargodiurnofestivo_amount_ant,
                        "payslip_id": self.id,
                        "input_type_id": recargodiurnofestivo_type_id_ant,
                        "code_input": 'RECARGODIURNOFESTIVO_ANT30',
                        "name_input": 'Horas Recargo Diurno Festivo (75%) Mes Anterior',
                    })
                if not recargonocturnofestivo_amount_ant == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": recargonocturnofestivo_amount_ant,
                        "payslip_id": self.id,
                        "input_type_id": recargonocturnofestivo_type_id_ant,
                        "code_input": 'RECARGONOCTURNOFESTIVO_ANT30',
                        "name_input": 'Horas Recargo Nocturno Festivo (110%) Mes Anterior',
                    })

            # Horas extras promedio 12 meses atras
            horas_extras_12month_before = self.get_inputs_hora_extra_12month_before(contract, date_from, date_to)
            if horas_extras_12month_before:
                hm12_date_ini = date_to - relativedelta(months=12)
                hm12_date_ini = hm12_date_ini + relativedelta(days=1)
                if contract.date_start <= hm12_date_ini:
                    hm12_date_init = hm12_date_ini
                else:
                    hm12_date_init = contract.date_start
                #total_days12y = days_between(hm12_date_init, date_to)
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_days12y = days360(hm12_date_init, date_to) + 1

                if total_days12y < 30:
                    day_base = total_days12y
                else:
                    day_base = 30

                extradiurna_amount = 0
                extradiurnafestivo_amount = 0
                extranocturna_amount = 0
                extranocturnafestivo_amount = 0
                recargonocturno_amount = 0
                recargodiurnofestivo_amount = 0
                recargonocturnofestivo_amount = 0
                for hora in horas_extras_12month_before:
                    if hora[1] == 'EXTRADIURNA':
                        extradiurna_amount = extradiurna_amount + hora[2]
                        extradiurna_type_id = hora[3]
                    if hora[1] == 'EXTRADIURNAFESTIVO':
                        extradiurnafestivo_amount = extradiurnafestivo_amount + hora[2]
                        extradiurnafestivo_type_id = hora[3]
                    if hora[1] == 'EXTRANOCTURNA':
                        extranocturna_amount = extranocturna_amount + hora[2]
                        extranocturna_type_id = hora[3]
                    if hora[1] == 'EXTRANOCTURNAFESTIVO':
                        extranocturnafestivo_amount = extranocturnafestivo_amount + hora[2]
                        extranocturnafestivo_type_id = hora[3]
                    if hora[1] == 'RECARGONOCTURNO':
                        recargonocturno_amount = recargonocturno_amount + hora[2]
                        recargonocturno_type_id = hora[3]
                    if hora[1] == 'RECARGODIURNOFESTIVO':
                        recargodiurnofestivo_amount = recargodiurnofestivo_amount + hora[2]
                        recargodiurnofestivo_type_id = hora[3]
                    if hora[1] == 'RECARGONOCTURNOFESTIVO':
                        recargonocturnofestivo_amount = recargonocturnofestivo_amount + hora[2]
                        recargonocturnofestivo_type_id = hora[3]

                if not extradiurna_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (extradiurna_amount/total_days12y)*day_base,
                        "payslip_id": self.id,
                        "input_type_id": extradiurna_type_id,
                        "code_input": 'EXTRADIURNA_PYEARS',
                        "name_input": 'Horas Extra Diurna (25%) Promedio 12M atras',
                    })
                if not extradiurnafestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (extradiurnafestivo_amount/total_days12y)*day_base,
                        "payslip_id": self.id,
                        "input_type_id": extradiurnafestivo_type_id,
                        "code_input": 'EXTRADIURNAFESTIVO_PYEARS',
                        "name_input": '	Horas Extra Diurna Festivo (100%) Promedio 12M atras',
                    })
                if not extranocturna_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (extranocturna_amount/total_days12y)*day_base,
                        "payslip_id": self.id,
                        "input_type_id": extranocturna_type_id,
                        "code_input": 'EXTRANOCTURNA_PYEARS',
                        "name_input": 'Horas Extra Nocturna (75%) Promedio 12M atras',
                    })
                if not extranocturnafestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (extranocturnafestivo_amount/total_days12y)*day_base,
                        "payslip_id": self.id,
                        "input_type_id": extranocturnafestivo_type_id,
                        "code_input": 'EXTRANOCTURNAFESTIVO_PYEARS',
                        "name_input": 'Horas Extra Nocturna Festivo (150%) Promedio 12M atras',
                    })
                if not recargonocturno_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (recargonocturno_amount/total_days12y)*day_base,
                        "payslip_id": self.id,
                        "input_type_id": recargonocturno_type_id,
                        "code_input": 'RECARGONOCTURNO_PYEARS',
                        "name_input": 'Horas Recargo Nocturno (35%) Promedio 12M atras',
                    })
                if not recargodiurnofestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (recargodiurnofestivo_amount/total_days12y)*day_base,
                        "payslip_id": self.id,
                        "input_type_id": recargodiurnofestivo_type_id,
                        "code_input": 'RECARGODIURNOFESTIVO_PYEARS',
                        "name_input": 'Horas Recargo Diurno Festivo (75%) Promedio 12M atras',
                    })
                if not recargonocturnofestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (recargonocturnofestivo_amount/total_days12y)*day_base,
                        "payslip_id": self.id,
                        "input_type_id": recargonocturnofestivo_type_id,
                        "code_input": 'RECARGONOCTURNOFESTIVO_PYEARS',
                        "name_input": 'Horas Recargo Nocturno Festivo (110%) Promedio 12M atras',
                    })

            # Horas extras promedio anual
            hora_extra_year_now = self.get_inputs_hora_extra_year_now(contract, date_from, date_to)
            if hora_extra_year_now:
                hdate_init_year = date(date_from.year, 1, 1)
                if contract.date_start <= hdate_init_year:
                    hdate_init = hdate_init_year
                else:
                    hdate_init = contract.date_start
                #total_days = days_between(hdate_init, date_to)
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_days = days360(hdate_init, date_to) + 1

                if total_days < 30:
                    day_base = total_days
                else:
                    day_base = 30

                extradiurna_amount = 0
                extradiurnafestivo_amount = 0
                extranocturna_amount = 0
                extranocturnafestivo_amount = 0
                recargonocturno_amount = 0
                recargodiurnofestivo_amount = 0
                recargonocturnofestivo_amount = 0
                for hora in hora_extra_year_now:
                    if hora[1] == 'EXTRADIURNA':
                        extradiurna_amount = extradiurna_amount + hora[2]
                        extradiurna_type_id = hora[3]
                    if hora[1] == 'EXTRADIURNAFESTIVO':
                        extradiurnafestivo_amount = extradiurnafestivo_amount + hora[2]
                        extradiurnafestivo_type_id = hora[3]
                    if hora[1] == 'EXTRANOCTURNA':
                        extranocturna_amount = extranocturna_amount + hora[2]
                        extranocturna_type_id = hora[3]
                    if hora[1] == 'EXTRANOCTURNAFESTIVO':
                        extranocturnafestivo_amount = extranocturnafestivo_amount + hora[2]
                        extranocturnafestivo_type_id = hora[3]
                    if hora[1] == 'RECARGONOCTURNO':
                        recargonocturno_amount = recargonocturno_amount + hora[2]
                        recargonocturno_type_id = hora[3]
                    if hora[1] == 'RECARGODIURNOFESTIVO':
                        recargodiurnofestivo_amount = recargodiurnofestivo_amount + hora[2]
                        recargodiurnofestivo_type_id = hora[3]
                    if hora[1] == 'RECARGONOCTURNOFESTIVO':
                        recargonocturnofestivo_amount = recargonocturnofestivo_amount + hora[2]
                        recargonocturnofestivo_type_id = hora[3]

                if not extradiurna_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (extradiurna_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": extradiurna_type_id,
                        "code_input": 'EXTRADIURNA_YEARS_NOW',
                        "name_input": 'Horas Extra Diurna (25%) Promedio Anual',
                    })
                if not extradiurnafestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (extradiurnafestivo_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": extradiurnafestivo_type_id,
                        "code_input": 'EXTRADIURNAFESTIVO_YEARS_NOW',
                        "name_input": '	Horas Extra Diurna Festivo (100%) Promedio Anual',
                    })
                if not extranocturna_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (extranocturna_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": extranocturna_type_id,
                        "code_input": 'EXTRANOCTURNA_YEARS_NOW',
                        "name_input": 'Horas Extra Nocturna (75%) Promedio Anual',
                    })
                if not extranocturnafestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (extranocturnafestivo_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": extranocturnafestivo_type_id,
                        "code_input": 'EXTRANOCTURNAFESTIVO_YEARS_NOW',
                        "name_input": 'Horas Extra Nocturna Festivo (150%) Promedio Anual',
                    })
                if not recargonocturno_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (recargonocturno_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": recargonocturno_type_id,
                        "code_input": 'RECARGONOCTURNO_YEARS_NOW',
                        "name_input": 'Horas Recargo Nocturno (35%) Promedio Anual',
                    })
                if not recargodiurnofestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (recargodiurnofestivo_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": recargodiurnofestivo_type_id,
                        "code_input": 'RECARGODIURNOFESTIVO_YEARS_NOW',
                        "name_input": 'Horas Recargo Diurno Festivo (75%) Promedio Anual',
                    })
                if not recargonocturnofestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (recargonocturnofestivo_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": recargonocturnofestivo_type_id,
                        "code_input": 'RECARGONOCTURNOFESTIVO_YEARS_NOW',
                        "name_input": 'Horas Recargo Nocturno Festivo (110%) Promedio Anual',
                    })

            # Horas extras promedio semestral
            hora_extra_6month = self.get_inputs_hora_extra_6month(contract, date_from, date_to)
            if hora_extra_6month:
                if self.date_from.month <= 6 and self.date_from.day <= 31:
                    hdate_init_6month = date(self.date_from.year, 1, 1)

                elif self.date_from.month <= 12 and self.date_from.day <= 31:
                    hdate_init_6month = date(self.date_from.year, 7, 1)

                if contract.date_start <= hdate_init_6month:
                    hdate_init = hdate_init_6month
                else:
                    hdate_init = contract.date_start

                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)

                total_days = days360(hdate_init, date_to) + 1

                if total_days < 30:
                    day_base = total_days
                else:
                    day_base = 30

                extradiurna_amount = 0
                extradiurnafestivo_amount = 0
                extranocturna_amount = 0
                extranocturnafestivo_amount = 0
                recargonocturno_amount = 0
                recargodiurnofestivo_amount = 0
                recargonocturnofestivo_amount = 0
                for hora in hora_extra_6month:
                    if hora[1] == 'EXTRADIURNA':
                        extradiurna_amount = extradiurna_amount + hora[2]
                        extradiurna_type_id = hora[3]
                    if hora[1] == 'EXTRADIURNAFESTIVO':
                        extradiurnafestivo_amount = extradiurnafestivo_amount + hora[2]
                        extradiurnafestivo_type_id = hora[3]
                    if hora[1] == 'EXTRANOCTURNA':
                        extranocturna_amount = extranocturna_amount + hora[2]
                        extranocturna_type_id = hora[3]
                    if hora[1] == 'EXTRANOCTURNAFESTIVO':
                        extranocturnafestivo_amount = extranocturnafestivo_amount + hora[2]
                        extranocturnafestivo_type_id = hora[3]
                    if hora[1] == 'RECARGONOCTURNO':
                        recargonocturno_amount = recargonocturno_amount + hora[2]
                        recargonocturno_type_id = hora[3]
                    if hora[1] == 'RECARGODIURNOFESTIVO':
                        recargodiurnofestivo_amount = recargodiurnofestivo_amount + hora[2]
                        recargodiurnofestivo_type_id = hora[3]
                    if hora[1] == 'RECARGONOCTURNOFESTIVO':
                        recargonocturnofestivo_amount = recargonocturnofestivo_amount + hora[2]
                        recargonocturnofestivo_type_id = hora[3]

                if not extradiurna_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (extradiurna_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": extradiurna_type_id,
                        "code_input": 'EXTRADIURNA_6MONTH',
                        "name_input": 'Horas Extra Diurna (25%) Promedio Semestral',
                    })
                if not extradiurnafestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (extradiurnafestivo_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": extradiurnafestivo_type_id,
                        "code_input": 'EXTRADIURNAFESTIVO_6MONTH',
                        "name_input": '	Horas Extra Diurna Festivo (100%) Promedio Semestral',
                    })
                if not extranocturna_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (extranocturna_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": extranocturna_type_id,
                        "code_input": 'EXTRANOCTURNA_6MONTH',
                        "name_input": 'Horas Extra Nocturna (75%) Promedio Semestral',
                    })
                if not extranocturnafestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (extranocturnafestivo_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": extranocturnafestivo_type_id,
                        "code_input": 'EXTRANOCTURNAFESTIVO_6MONTH',
                        "name_input": 'Horas Extra Nocturna Festivo (150%) Promedio Semestral',
                    })
                if not recargonocturno_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (recargonocturno_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": recargonocturno_type_id,
                        "code_input": 'RECARGONOCTURNO_6MONTH',
                        "name_input": 'Horas Recargo Nocturno (35%) Promedio Semestral',
                    })
                if not recargodiurnofestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (recargodiurnofestivo_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": recargodiurnofestivo_type_id,
                        "code_input": 'RECARGODIURNOFESTIVO_6MONTH',
                        "name_input": 'Horas Recargo Diurno Festivo (75%) Promedio Semestral',
                    })
                if not recargonocturnofestivo_amount == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (recargonocturnofestivo_amount / total_days) * day_base,
                        "payslip_id": self.id,
                        "input_type_id": recargonocturnofestivo_type_id,
                        "code_input": 'RECARGONOCTURNOFESTIVO_6MONTH',
                        "name_input": 'Horas Recargo Nocturno Festivo (110%) Promedio Semestral',
                    })

            loans_fijos_ids = self.get_inputs_loans_fijos(contract)
            if loans_fijos_ids:
                for hora in loans_fijos_ids:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": hora[2],
                        "payslip_id": self.id,
                        "input_type_id": hora[3],
                        "code_input": hora[1],
                        "name_input": hora[0],
                    })

            # Bonificaciones descuentos reintegro y comisiones
            loans_ids = self.get_inputs_loans(contract, date_from, date_to)
            if loans_ids:
                amountb = 0
                inputb_type_id = 0
                amountd = 0
                inputd_type_id = 0
                amountrip = 0
                inputrip_type_id = 0
                amountric = 0
                inputric_type_id = 0
                amount_aux_movi = 0
                input_aux_movi_type_id = 0
                amount_aux_fun = 0
                input_aux_fun_type_id = 0
                amount_fyc = 0
                input_fyc_type_id = 0
                amountc = 0
                inputc_type_id = 0
                for loans in loans_ids:
                    if loans[1] == 'BONIFICACION':
                       amountb = amountb + loans[2]
                       inputb_type_id = loans[3]
                       nameb = loans[0]
                       codeb = loans[1]
                    if loans[1] == 'DESCUENTOS':
                       amountd = amountd + loans[2]
                       inputd_type_id = loans[3]
                       named = loans[0]
                       coded = loans[1]
                    if loans[1] == 'REINTEGRO_PAGAR':
                       amountrip = amountrip + loans[2]
                       inputrip_type_id = loans[3]
                       namerip = loans[0]
                       coderip = loans[1]
                    if loans[1] == 'REINTEGRO_COBRAR':
                       amountric = amountric + loans[2]
                       inputric_type_id = loans[3]
                       nameric = loans[0]
                       coderic = loans[1]
                    if loans[1] == 'AUX_MOVILIZACION':
                       amount_aux_movi = amount_aux_movi + loans[2]
                       input_aux_movi_type_id = loans[3]
                       name_aux_movi = loans[0]
                       code_aux_movi = loans[1]
                    if loans[1] == 'AUX_FUNERARIO':
                        amount_aux_fun = amount_aux_fun + loans[2]
                        input_aux_fun_type_id = loans[3]
                        name_aux_fun = loans[0]
                        code_aux_fun = loans[1]
                    if loans[1] == 'FYC':
                        amount_fyc = amount_fyc + loans[2]
                        input_fyc_type_id = loans[3]
                        name_fyc = loans[0]
                        code_fyc = loans[1]
                    if loans[1] == 'COMISION':
                       amountc = amountc + loans[2]
                       inputc_type_id = loans[3]
                       namec = loans[0]
                       codec = loans[1]

                if not amountb == 0:
                    self.env['hr.payslip.input'].create({
                     "sequence": 1,
                     "amount": amountb,
                     "payslip_id": self.id,
                     "input_type_id": inputb_type_id,
                     "name_input": nameb,
                     "code_input": codeb,
                    })
                if not amountd == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amountd,
                        "payslip_id": self.id,
                        "input_type_id": inputd_type_id,
                        "name_input": named,
                        "code_input": coded,
                    })
                if not amountrip == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amountrip,
                        "payslip_id": self.id,
                        "input_type_id": inputrip_type_id,
                        "name_input": namerip,
                        "code_input": coderip,
                    })
                if not amountric == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amountric,
                        "payslip_id": self.id,
                        "input_type_id": inputric_type_id,
                        "name_input": nameric,
                        "code_input": coderic,
                    })
                if not amount_aux_movi == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amount_aux_movi,
                        "payslip_id": self.id,
                        "input_type_id": input_aux_movi_type_id,
                        "name_input": name_aux_movi,
                        "code_input": code_aux_movi,
                    })
                if not amount_aux_fun == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amount_aux_fun,
                        "payslip_id": self.id,
                        "input_type_id": input_aux_fun_type_id,
                        "name_input": name_aux_fun,
                        "code_input": code_aux_fun,
                    })
                if not amount_fyc == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amount_fyc,
                        "payslip_id": self.id,
                        "input_type_id": input_fyc_type_id,
                        "name_input": name_fyc,
                        "code_input": code_fyc,
                    })
                if not amountc == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amountc,
                        "payslip_id": self.id,
                        "input_type_id": inputc_type_id,
                        "name_input": namec,
                        "code_input": codec,
                    })

            # Bonificaciones y comisiones Mes actual
            loans_month_now_ids = self.get_inputs_loans_month_now(contract, date_from, date_to)
            if loans_month_now_ids and date_from.day == 16:
                amountbn = 0
                inputbn_type_id = 0
                amountc = 0
                inputc_type_id = 0
                for loans in loans_month_now_ids:
                    if loans[1] == 'BONIFICACION':
                        amountbn = amountbn + loans[2]
                        inputbn_type_id = loans[3]
                    if loans[1] == 'COMISION':
                        amountc = amountc + loans[2]
                        inputc_type_id = loans[3]
                if not amountbn == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amountbn,
                        "payslip_id": self.id,
                        "input_type_id": inputbn_type_id,
                        "code_input": 'BONIFICACION_NOW30',
                        "name_input": 'Bonificación Mes Actual',
                    })
                if not amountc == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amountc,
                        "payslip_id": self.id,
                        "input_type_id": inputc_type_id,
                        "code_input": 'COMISION_NOW30',
                        "name_input": 'Comision Mes Actual',
                    })

            # Bonificaciones comisiones y descuentos Mes anterior
            loans_month_before_ids = self.get_inputs_loans_month_before(contract, date_from, date_to)
            if loans_month_before_ids:
                amountb = 0
                inputb_type_id = 0
                amountd = 0
                inputd_type_id = 0
                amountc = 0
                inputc_type_id = 0
                for loans in loans_month_before_ids:
                    if loans[1] == 'BONIFICACION':
                       amountb = amountb + loans[2]
                       inputb_type_id = loans[3]
                    if loans[1] == 'DESCUENTOS':
                       amountd = amountd + loans[2]
                       inputd_type_id = loans[3]
                    if loans[1] == 'COMISION':
                       amountc = amountc + loans[2]
                       inputc_type_id = loans[3]
                if not amountb == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amountb,
                        "payslip_id": self.id,
                        "input_type_id": inputb_type_id,
                        "code_input": 'BONIFICACION_ANT30',
                        "name_input": 'Bonificación Mes Anterior',
                    })
                if not amountc == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amountc,
                        "payslip_id": self.id,
                        "input_type_id": inputc_type_id,
                        "code_input": 'COMISION_ANT30',
                        "name_input": 'Comision Mes Anterior',
                    })
                if not amountd == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amountd,
                        "payslip_id": self.id,
                        "input_type_id": inputd_type_id,
                        "code_input": 'DESCUENTO_ANT30',
                        "name_input": 'Descuento Mes Anterior',
                    })

            # Bonificaciones y comisiones 12 meses atras
            inputs_loans_12month_before = self.get_inputs_loans_12month_before(contract, date_from, date_to)
            if inputs_loans_12month_before:
                lm12_date_ini = date_to - relativedelta(months=12)
                lm12_date_ini = lm12_date_ini + relativedelta(days=1)
                if contract.date_start <= lm12_date_ini:
                    lm12_date_init = lm12_date_ini
                else:
                    lm12_date_init = contract.date_start
                #total_dayl12 = days_between(lm12_date_init, date_to)
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_dayl12 = days360(lm12_date_init, date_to)+1

                if total_dayl12 < 30:
                    day_base = total_dayl12
                else:
                    day_base = 30

                countb = 0
                amountb = 0
                inputb_type_id = 0
                countc = 0
                amountc = 0
                inputc_type_id = 0
                for loans in inputs_loans_12month_before:
                    if loans[1] == 'BONIFICACION':
                        countb = countb + 1
                        amountb = amountb + loans[2]
                        inputb_type_id = loans[3]
                    if loans[1] == 'COMISION':
                        countc = countc + 1
                        amountc = amountc + loans[2]
                        inputc_type_id = loans[3]
                if not amountb == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amountb/total_dayl12)*day_base,
                        "payslip_id": self.id,
                        "input_type_id": inputb_type_id,
                        "code_input": 'BONIFICACION_PYEARS',
                        "name_input": 'Bonificación Promedio (12M atras)',
                    })
                if not amountc == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amountc/total_dayl12)*day_base,
                        "payslip_id": self.id,
                        "input_type_id": inputc_type_id,
                        "code_input": 'COMISION_PYEARS',
                        "name_input": 'Comision Promedio (12M atras)',
                    })

            # Bonificaciones y comisiones anual
            loans_year_now = self.get_inputs_loans_year_now(contract, date_from, date_to)
            if loans_year_now:
                ldate_init_year = date(date_from.year, 1, 1)
                if contract.date_start <= ldate_init_year:
                    ldate_init = ldate_init_year
                else:
                    ldate_init = contract.date_start
                #ltotal_days = days_between(ldate_init, date_to)
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                ltotal_days = days360(ldate_init, date_to) + 1

                if ltotal_days < 30:
                    day_base = ltotal_days
                else:
                    day_base = 30

                countb = 0
                amountb = 0
                inputb_type_id = 0
                countc = 0
                amountc = 0
                inputc_type_id = 0
                for loans in loans_year_now:
                    if loans[1] == 'BONIFICACION':
                        countb = countb + 1
                        amountb = amountb + loans[2]
                        inputb_type_id = loans[3]
                    if loans[1] == 'COMISION':
                        countc = countc + 1
                        amountc = amountc + loans[2]
                        inputc_type_id = loans[3]
                if not amountb == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amountb/ltotal_days)*day_base,
                        "payslip_id": self.id,
                        "input_type_id": inputb_type_id,
                        "code_input": 'BONIFICACION_YEARS_NOW',
                        "name_input": 'Bonificación Promedio Anual',
                    })
                if not amountc == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amountc/ltotal_days)*day_base,
                        "payslip_id": self.id,
                        "input_type_id": inputc_type_id,
                        "code_input": 'COMISION_YEARS_NOW',
                        "name_input": 'Comision Promedio Anual',
                    })

            # Bonificaciones y comisiones semestral
            loans_6month = self.get_inputs_loans_6month(contract, date_from, date_to)
            if loans_6month:
                if self.date_from.month <= 6 and self.date_from.day <= 31:
                    ldate_init_6month = date(self.date_from.year, 1, 1)

                elif self.date_from.month <= 12 and self.date_from.day <= 31:
                    ldate_init_6month = date(self.date_from.year, 7, 1)

                if contract.date_start <= ldate_init_6month:
                    ldate_init = ldate_init_6month
                else:
                    ldate_init = contract.date_start
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)

                ltotal_days = days360(ldate_init, date_to) + 1

                if ltotal_days < 30:
                    day_base = ltotal_days
                else:
                    day_base = 30

                countb = 0
                amountb = 0
                inputb_type_id = 0
                countc = 0
                amountc = 0
                inputc_type_id = 0
                for loans in loans_6month:
                    if loans[1] == 'BONIFICACION':
                        countb = countb + 1
                        amountb = amountb + loans[2]
                        inputb_type_id = loans[3]
                    if loans[1] == 'COMISION':
                        countc = countc + 1
                        amountc = amountc + loans[2]
                        inputc_type_id = loans[3]
                if not amountb == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amountb/ltotal_days)*day_base,
                        "payslip_id": self.id,
                        "input_type_id": inputb_type_id,
                        "code_input": 'BONIFICACION_6MONTH',
                        "name_input": 'Bonificación Promedio Semestral',
                    })
                if not amountc == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amountc/ltotal_days)*day_base,
                        "payslip_id": self.id,
                        "input_type_id": inputc_type_id,
                        "code_input": 'COMISION_6MONTH',
                        "name_input": 'Comision Promedio Semestral',
                    })

            # Auxilio de transporte anual
            amount_transport_subsidy_pyear = self.get_amount_transport_subsidy_year(contract, date_from, date_to)
            if amount_transport_subsidy_pyear and amount_transport_subsidy_pyear > 0:
                code_aux_transp = self.env['hr.payslip.input.type'].search([("code", "=", 'AUX_TRANSPORTE_PYEARS')],
                                                                           limit=1).id
                self.env['hr.payslip.input'].create({
                    "sequence": 1,
                    "amount": amount_transport_subsidy_pyear,
                    "payslip_id": self.id,
                    "input_type_id": code_aux_transp if code_aux_transp else inputb_type_id,
                    "code_input": 'AUX_TRANSPORTE_PYEARS',
                    "name_input": 'Auxilio de Transporte Promedio Anual',
                })

            # Total Ingresos Primera Quincena
            get_inputs_total_ingreso = self.get_inputs_total_ingreso(contract, date_from, date_to)
            if get_inputs_total_ingreso and date_from.day == 16:
                total_ingreso_type = self.env['hr.payslip.input.type'].search([("code", "=", 'NET115')], limit=1).id
                if total_ingreso_type:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": get_inputs_total_ingreso.total,
                        "payslip_id": self.id,
                        "input_type_id": total_ingreso_type,
                        "code_input": 'NET115',
                        "name_input": 'Total Ingresos (1 Quincena)',
                    })

            # Auxilio de Movilizacion Primera Quincena
            get_inputs_aux_movilizacion = self.get_inputs_aux_movilizacion(contract, date_from, date_to)
            if get_inputs_aux_movilizacion and date_from.day == 16:
                aux_movilizacion_type = self.env['hr.payslip.input.type'].search([("code", "=", 'AUX_MOVILIZACION')], limit=1).id
                if aux_movilizacion_type:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": get_inputs_aux_movilizacion.total,
                        "payslip_id": self.id,
                        "input_type_id": aux_movilizacion_type,
                        "code_input": 'AUX_MOVILIZACION',
                        "name_input": 'Auxilio de Movilización (1 Quincena)',
                    })

            # Auxilio Rodamiento Primera Quincena
            get_inputs_aux_rodamiento = self.get_inputs_aux_rodamiento(contract, date_from, date_to)
            if get_inputs_aux_rodamiento and date_from.day == 16:
                aux_rodamiento_type = self.env['hr.payslip.input.type'].search([("code", "=", 'AUX_RODAMIENTO')], limit=1).id
                if aux_rodamiento_type:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": get_inputs_aux_rodamiento.total,
                        "payslip_id": self.id,
                        "input_type_id": aux_rodamiento_type,
                        "code_input": 'AUX_RODAMIENTO',
                        "name_input": 'Auxilio de Rodamiento (1 Quincena)',
                    })

            # Total Deduciones para retencion en la fuente
            if contract.retention_method == 'M1':
                # Deducciones
                inputs_withholding_tax = self.get_inputs_withholding_tax(contract, date_from, date_to)
                date_month_now_from = date(date_from.year, date_from.month, 1)
                date_month_next = date_month_now_from + relativedelta(months=1)
                date_month_now_to = date(date_month_next.year, date_month_next.month, 1) - relativedelta(days=1)
                item_tax = inputs_withholding_tax.deductions_rt_id.search([("deductions_id", "=", inputs_withholding_tax.id),
                                                                        '&', ("date", ">=", date_month_now_from),("date", "<=", date_month_now_to)])
                if item_tax:
                   amount_rtf = 0
                   for d in item_tax:
                       amount_rtf = amount_rtf + d.amount
                   self.env['hr.payslip.input'].create({
                       "sequence": 1,
                       "amount": amount_rtf,
                       "payslip_id": self.id,
                       "input_type_id": inputs_withholding_tax.input_id.id,
                       "code_input": inputs_withholding_tax.input_id.code,
                       "name_input": inputs_withholding_tax.input_id.name,
                   })

                # Renta Exenta
                inputs_exempt_income_tax = self.get_inputs_exempt_income_tax(contract, date_from, date_to)
                date_month_now_from = date(date_from.year, date_from.month, 1)
                date_month_next = date_month_now_from + relativedelta(months=1)
                date_month_now_to = date(date_month_next.year, date_month_next.month, 1) - relativedelta(days=1)
                item_exempt_income_tax = inputs_exempt_income_tax.exempt_income_id.search(
                    [("exempt_income_id", "=", inputs_exempt_income_tax.id),
                     '&', ("date", ">=", date_month_now_from), ("date", "<=", date_month_now_to)])
                if item_exempt_income_tax:
                    amount_rtf = 0
                    for d in item_exempt_income_tax:
                        amount_rtf = amount_rtf + d.amount
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amount_rtf,
                        "payslip_id": self.id,
                        "input_type_id": inputs_exempt_income_tax.input_id.id,
                        "code_input": inputs_exempt_income_tax.input_id.code,
                        "name_input": inputs_exempt_income_tax.input_id.name,
                    })

        return res

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        self.company_id = employee.company_id
        if not self.contract_id or self.employee_id != self.contract_id.employee_id: # Add a default contract if not already defined
            contracts = employee._get_contracts(date_from, date_to)

            if not contracts or not contracts[0].structure_type_id.default_struct_id:
                self.contract_id = False
                self.struct_id = False
                return
            self.contract_id = contracts[0]
            self.struct_id = contracts[0].structure_type_id.default_struct_id

        payslip_name = self.struct_id.payslip_name or _('Salary Slip')
        self.name = '%s - %s - %s' % (payslip_name, self.employee_id.name or '', format_date(self.env, self.date_from, date_format="MMMM y"))

        if date_to > date_utils.end_of(fields.Date.today(), 'month'):
            self.warning_message = _("This payslip can be erroneous! Work entries may not be generated for the period from %s to %s." %
                (date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1), date_to))
        else:
            self.warning_message = False

        self.worked_days_line_ids = self._get_new_worked_days_lines()


    def _get_worked_day_lines(self):
        """
        :returns: a list of dict containing the worked days values that should be applied for the given payslip
        """
        res = []
        # fill only if the contract as a working schedule linked
        self.ensure_one()
        contract = self.contract_id
        if contract.resource_calendar_id:
            paid_amount = self._get_contract_wage()
            wage_min  = self.env['hr.salary.rule'].search([("code", "=", 'SMLMV')], limit=1).amount_fix
            paid_amount_ant = paid_amount
            unpaid_work_entry_types = self.struct_id.unpaid_work_entry_type_ids.ids
            work_hours = contract._get_work_hours(self.date_from, self.date_to)
            exceed_hours = contract._get_exceed_hours(self.date_from, self.date_to)
            total_hours = sum(work_hours.values()) or 1
            work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
            biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
            add_days_rounding = 0
            print ('-------444', work_hours_ordered, work_hours, total_hours)
            novelties_days = 0
            if self.date_from != self.date_to:
                for work_entry_type_id, hours in work_hours_ordered:
                    work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
                    is_paid = work_entry_type_id not in unpaid_work_entry_types
                    calendar = contract.resource_calendar_id
                    print ('-------', hours)
                    days = round(hours / calendar.hours_per_day, 5) if calendar.hours_per_day else 0
                    if work_entry_type_id == biggest_work:
                        days += add_days_rounding
                    day_rounded = self._round_days(work_entry_type, days)
                    add_days_rounding += (days - day_rounded)
                    if day_rounded > 15:
                        day_rounded = 15
                    attendance_line = {
                        'sequence': work_entry_type.sequence,
                        'work_entry_type_id': work_entry_type_id,
                        'name': work_entry_type.code,
                        'number_of_days': day_rounded,
                        'number_of_hours': hours,
                        'number_of_days_total': day_rounded,
                        'number_of_hours_total': hours,
                        'amount': 0,
                    }
                    assistance_type = self.env['hr.work.entry.type'].search([("code", "=", 'WORK100')], limit=1)
                    if not work_entry_type_id == assistance_type.id:
                        res.append(attendance_line)
                        novelties_days += day_rounded

                    if novelties_days > 15:
                        novelties_days = 15

                        # Dias por rango de fecha (manejo de 30 dias)
                all_days = days_between(self.date_from, self.date_to)

                # Dias de asistencia
                assistance_days = all_days - novelties_days
                assistance_hours = assistance_days * contract.resource_calendar_id.hours_per_day
                work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'WORK100')], limit=1)
                attendance_assistance = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'name': work_entry_type.code,
                    'number_of_days': assistance_days,
                    'number_of_hours': assistance_hours,
                    'number_of_days_total': assistance_days,
                    'number_of_hours_total': assistance_hours,
                    'amount': 0,
                }
                if not assistance_days == 0:
                    res.append(attendance_assistance)

                # Dias totales
                total_days = assistance_days + novelties_days
                total_hours = total_days * contract.resource_calendar_id.hours_per_day
                work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'TOTALDAYS')], limit=1)
                attendances_total = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'name': work_entry_type.code,
                    'number_of_days': total_days,
                    'number_of_hours': total_hours,
                    'number_of_days_total': total_days,
                    'number_of_hours_total': total_hours,
                    'amount': 0,
                }
                res.append(attendances_total)


                # Dias de vacaciones en dinero
                vacations_money = self.env['hr.leave'].search([('employee_id', '=', self.employee_id.id),
                                                               ('holiday_status_id.code', '=', 'VACATIONS_MONEY'),
                                                               ("date_from", ">=", self.date_from),
                                                               ("date_to", "<=", self.date_to),
                                                               ('state', '=', 'validate')])
                if vacations_money:
                    vacations_money_days = vacations_money.number_of_days
                    vacations_money_amount = vacations_money.amount_vacations
                    vacations_money_hours = vacations_money_days * contract.resource_calendar_id.hours_per_day
                    work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'VACATIONS_MONEY')], limit=1)
                    vacations_money_assistance = {
                        'sequence': work_entry_type.sequence,
                        'work_entry_type_id': work_entry_type.id,
                        'name': work_entry_type.code,
                        'number_of_days': vacations_money_days,
                        'number_of_hours': vacations_money_hours,
                        'number_of_days_total': vacations_money_days,
                        'number_of_hours_total': vacations_money_hours,
                        'amount': vacations_money_amount,
                    }
                    res.append(vacations_money_assistance)

                # Dias de vacaciones en dinero a liquidar
                vacations_money_liq = self.env['hr.leave'].search([('employee_id', '=', self.employee_id.id),
                                                               ('holiday_status_id.code', '=', 'VACATIONS_MONEY_LIQ'),
                                                               ("date_from", ">=", self.date_from),
                                                               ("date_to", "<=", self.date_to),
                                                               ('state', '=', 'validate')])
                if vacations_money_liq:
                    vacations_money_liq_days = vacations_money_liq.number_of_days
                    vacations_money_liq_amount = vacations_money_liq.amount_vacations
                    vacations_money_liq_hours = vacations_money_liq_days * contract.resource_calendar_id.hours_per_day
                    work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'VACATIONS_MONEY_LIQ')],
                                                                            limit=1)
                    vacations_money_liq_assistance = {
                        'sequence': work_entry_type.sequence,
                        'work_entry_type_id': work_entry_type.id,
                        'name': work_entry_type.code,
                        'number_of_days': vacations_money_liq_days,
                        'number_of_hours': vacations_money_liq_hours,
                        'number_of_days_total': vacations_money_liq_days,
                        'number_of_hours_total': vacations_money_liq_hours,
                        'amount': vacations_money_liq_amount,
                    }
                    res.append(vacations_money_liq_assistance)


                # Dias anuales trabajados
                date_init_year = date(self.date_from.year, 1, 1)
                date_to = self.date_to
                if contract.date_start <= date_init_year:
                    date_init = date_init_year
                else:
                    date_init = contract.date_start
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_year_days = days360(date_init, date_to)+1
                suspensions_day = self.get_suspensions_day(contract, date_init, date_to)
                total_year_days = total_year_days - suspensions_day
                total_year_hours = total_year_days * contract.resource_calendar_id.hours_per_day
                work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'TOTALDAYSYEARS')], limit=1)
                attendances_year_total = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'name': work_entry_type.code,
                    'number_of_days': total_year_days,
                    'number_of_hours': total_year_hours,
                    'number_of_days_total': total_year_days,
                    'number_of_hours_total': total_year_hours,
                    'amount': 0,
                }
                res.append(attendances_year_total)

                # Dias semestrales trabajados

                if self.date_from.month <= 6 and self.date_from.day <= 31:
                    date_init_year = date(self.date_from.year, 1, 1)

                elif self.date_from.month <= 12 and self.date_from.day <= 31:
                    date_init_year = date(self.date_from.year, 7, 1)

                date_to = self.date_to
                if contract.date_start <= date_init_year:
                    date_init = date_init_year
                else:
                    date_init = contract.date_start
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_year_days = days360(date_init, date_to) + 1
                suspensions_day = self.get_suspensions_day(contract, date_init, date_to)
                total_year_days = total_year_days - suspensions_day
                total_year_hours = total_year_days * contract.resource_calendar_id.hours_per_day
                work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'TOTALDAYS6M')], limit=1)
                attendances_year_total = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'name': work_entry_type.code,
                    'number_of_days': total_year_days,
                    'number_of_hours': total_year_hours,
                    'number_of_days_total': total_year_days,
                    'number_of_hours_total': total_year_hours,
                    'amount': 0,
                }
                res.append(attendances_year_total)


                # Días trabajados desde inicio de contrato
                date_to = self.date_to
                date_init = contract.date_start
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_year_days = days360(date_init, date_to) + 1
                suspensions_day = self.get_suspensions_day(contract, date_init, date_to)
                total_year_days = total_year_days - suspensions_day
                total_year_hours = total_year_days * contract.resource_calendar_id.hours_per_day
                work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'TOTALDAYSCONTRACT')], limit=1)
                attendances_yearc_total = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'name': work_entry_type.code,
                    'number_of_days': total_year_days,
                    'number_of_hours': total_year_hours,
                    'number_of_days_total': total_year_days,
                    'number_of_hours_total': total_year_hours,
                    'amount': 0,
                }
                res.append(attendances_yearc_total)

                # Total ausencias por enfermedad
                absence_rate_2D = self.env['hr.payslip.input.type'].search([("code", "=", 'P_AUSENCIAS_2D')],limit=1).disability_percentage
                absence_rate_90D = self.env['hr.payslip.input.type'].search([("code", "=", 'P_AUSENCIAS_90D')],limit=1).disability_percentage
                absence_rate_M91D = self.env['hr.payslip.input.type'].search([("code", "=", 'P_AUSENCIAS_M91D')],limit=1).disability_percentage
                work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'INCAPACIDADGENERAL')], limit=1)
                leave_sickness_amount_total = 0
                leave_sickness_days_total = 0
                leave_sickness_hours_total = 0
                leave_days_t = 0
                leave_hours_t = 0
                wage_min_day = wage_min/30
                horas_extras_promedio12m_dia = 0
                recargo_promedio12m_dia = 0
                bonificacion_promedio12m_dia = 0
                comision_promedio12m_dia = 0

                inputs_loans_12month_before = self.get_inputs_loans_12month_before(contract, self.date_from, self.date_to)
                if inputs_loans_12month_before:
                    date_to = self.date_to
                    lm12_date_ini = self.date_to - relativedelta(months=12)
                    lm12_date_ini = lm12_date_ini + relativedelta(days=1)
                    if contract.date_start <= lm12_date_ini:
                        lm12_date_init = lm12_date_ini
                    else:
                        lm12_date_init = contract.date_start
                    # total_dayl12 = days_between(lm12_date_init, date_to)
                    if date_to.day == 31:
                        date_to = date_to - relativedelta(days=1)
                    total_dayl12 = days360(lm12_date_init, date_to) + 1
                    if total_dayl12 == 15:
                        day_base = 15
                    else:
                        day_base = 30
                    bonificacion_promedio12m = 0
                    comision_promedio12m = 0
                    for loans in inputs_loans_12month_before:
                        if loans[1] == 'BONIFICACION':
                            bonificacion_promedio12m = bonificacion_promedio12m + loans[2]
                        if loans[1] == 'COMISION':
                            comision_promedio12m = comision_promedio12m + loans[2]
                    if not bonificacion_promedio12m == 0:
                        bonificacion_promedio12m = (bonificacion_promedio12m / total_dayl12) * day_base
                    if not comision_promedio12m == 0:
                        comision_promedio12m = (comision_promedio12m / total_dayl12) * day_base

                    bonificacion_promedio12m_dia = ((bonificacion_promedio12m/total_dayl12)*30)/30
                    comision_promedio12m_dia = ((comision_promedio12m/total_dayl12)*30)/30

                horas_extras_12month_before = self.get_inputs_hora_extra_12month_before(contract, self.date_from, self.date_to)
                if horas_extras_12month_before:
                    date_to = self.date_to
                    hm12_date_ini = self.date_to - relativedelta(months=12)
                    hm12_date_ini = hm12_date_ini + relativedelta(days=1)
                    if contract.date_start <= hm12_date_ini:
                        hm12_date_init = hm12_date_ini
                    else:
                        hm12_date_init = contract.date_start
                    # total_days12y = days_between(hm12_date_init, date_to)
                    if date_to.day == 31:
                        date_to = date_to - relativedelta(days=1)
                    total_days12y = days360(hm12_date_init, date_to) + 1
                    if total_days12y == 15:
                        day_base = 15
                    else:
                        day_base = 30
                    extradiurna_promedio12m = 0
                    extradiurnafestivo_promedio12m = 0
                    extranocturna_promedio12m = 0
                    extranocturnafestivo_promedio12m = 0
                    recargonocturno_promedio12m = 0
                    recargodiurnofestivo_promedio12m = 0
                    recargonocturnofestivo_promedio12m = 0
                    for hora in horas_extras_12month_before:
                        if hora[1] == 'EXTRADIURNA':
                            extradiurna_promedio12m = extradiurna_promedio12m + hora[2]
                        if hora[1] == 'EXTRADIURNAFESTIVO':
                            extradiurnafestivo_promedio12m = extradiurnafestivo_promedio12m + hora[2]
                        if hora[1] == 'EXTRANOCTURNA':
                            extranocturna_promedio12m = extranocturna_promedio12m + hora[2]
                        if hora[1] == 'EXTRANOCTURNAFESTIVO':
                            extranocturnafestivo_promedio12m = extranocturnafestivo_promedio12m + hora[2]
                        if hora[1] == 'RECARGONOCTURNO':
                            recargonocturno_promedio12m = recargonocturno_promedio12m + hora[2]
                        if hora[1] == 'RECARGODIURNOFESTIVO':
                            recargodiurnofestivo_promedio12m = recargodiurnofestivo_promedio12m + hora[2]
                        if hora[1] == 'RECARGONOCTURNOFESTIVO':
                            recargonocturnofestivo_promedio12m = recargonocturnofestivo_promedio12m + hora[2]

                    if not extradiurna_promedio12m == 0:
                        extradiurna_promedio12m = (extradiurna_promedio12m / total_days12y) * day_base
                    if not extradiurnafestivo_promedio12m == 0:
                        extradiurnafestivo_promedio12m = (extradiurnafestivo_promedio12m / total_days12y) * day_base
                    if not extranocturna_promedio12m == 0:
                        extranocturna_promedio12m = (extranocturna_promedio12m / total_days12y) * day_base
                    if not extranocturnafestivo_promedio12m == 0:
                        extranocturnafestivo_promedio12m = (extranocturnafestivo_promedio12m / total_days12y) * day_base
                    if not recargonocturno_promedio12m == 0:
                        recargonocturno_promedio12m = (recargonocturno_promedio12m / total_days12y) * day_base
                    if not recargodiurnofestivo_promedio12m == 0:
                        recargodiurnofestivo_promedio12m = (recargodiurnofestivo_promedio12m / total_days12y) * day_base
                    if not recargonocturnofestivo_promedio12m == 0:
                        recargonocturnofestivo_promedio12m = (recargonocturnofestivo_promedio12m / total_days12y) * day_base

                    horas_extras_promedio12m = extradiurna_promedio12m+extradiurnafestivo_promedio12m+extranocturna_promedio12m+extranocturnafestivo_promedio12m
                    recargo_promedio12m = recargonocturno_promedio12m+recargodiurnofestivo_promedio12m+recargonocturnofestivo_promedio12m

                    horas_extras_promedio12m_dia = ((horas_extras_promedio12m/total_days12y)*30)/30
                    recargo_promedio12m_dia = ((recargo_promedio12m/total_days12y)*30)/30

                salario_contrato_dia = paid_amount / 30
                total_valor_promedio_dia = salario_contrato_dia+bonificacion_promedio12m_dia+comision_promedio12m_dia+horas_extras_promedio12m_dia+recargo_promedio12m_dia

                leave_sickness_all = self.env['hr.work.entry'].search([("date_start", ">=", self.date_from),
                                                                       ("date_stop", "<=", self.date_to),
                                                                       ("work_entry_type_id", "=",
                                                                        work_entry_type.id),
                                                                       ("employee_id", "=",
                                                                        contract.employee_id.id)])
                for l in leave_sickness_all.leave_id:
                    leave_days_total = l.number_of_days
                    leave_hours_total = l.number_of_days * contract.resource_calendar_id.hours_per_day
                    leave_sickness = self.env['hr.work.entry'].search([("date_start", ">=", self.date_from),
                                                                       ("date_stop", "<=", self.date_to),
                                                                       ("leave_id", "=", l.id),
                                                                       ])
                    leave_sickness_hours = 0
                    for s in leave_sickness:
                        leave_sickness_hours += s.duration

                    leave_sickness_days = leave_sickness_hours / contract.resource_calendar_id.hours_per_day

                    leave_sickness_base_amount = total_valor_promedio_dia

                    if leave_days_total >= 1 and leave_days_total <= 2:
                        leave_sickness_amount_base = round((leave_sickness_base_amount*absence_rate_2D)/100)
                    elif leave_days_total >= 3 and leave_days_total <= 90:
                        leave_sickness_amount_base = round((leave_sickness_base_amount*absence_rate_90D)/100)
                    elif leave_days_total >= 91 and leave_days_total <= 180:
                        leave_sickness_amount_base = round((leave_sickness_base_amount*absence_rate_M91D)/100)
                    else:
                        leave_sickness_amount_base = 0

                    leave_sickness_amount = leave_sickness_amount_base * leave_sickness_days

                    if leave_sickness_amount_base < wage_min_day and leave_sickness_amount_base != 0:
                        leave_sickness_amount = wage_min_day * leave_sickness_days


                    work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'LEAVE110L')], limit=1)
                    leave_s = {
                        'sequence': work_entry_type.sequence,
                        'work_entry_type_id': work_entry_type.id,
                        'name': work_entry_type.code,
                        'number_of_days': leave_sickness_days,
                        'number_of_hours': leave_sickness_hours,
                        'number_of_days_total': leave_days_total,
                        'number_of_hours_total': leave_hours_total,
                        'amount': leave_sickness_amount,
                    }
                    leave_sickness_days_total += leave_sickness_days
                    leave_sickness_hours_total += leave_sickness_hours
                    leave_days_t += leave_days_total
                    leave_hours_t += leave_hours_total
                    leave_sickness_amount_total += leave_sickness_amount
                    res.append(leave_s)

                # Total de ausencia por enfermedad
                work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'TOTALAE')], limit=1)
                totalae = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'name': work_entry_type.code,
                    'number_of_days': leave_sickness_days_total,
                    'number_of_hours': leave_sickness_hours_total,
                    'number_of_days_total': leave_days_t,
                    'number_of_hours_total': leave_hours_t,
                    'amount': leave_sickness_amount_total,
                }
                if not leave_sickness_days_total == 0:
                    res.append(totalae)

                # Dias Licencia Maternidad

                lmaternidad_all = self.env['hr.work.entry'].search([("date_start", ">=", self.date_from),
                                                                       ("date_stop", "<=", self.date_to),
                                                                       ("work_entry_type_id.code", "=",
                                                                        'LICENCIAMATERNIDAD'),
                                                                       ("employee_id", "=",
                                                                        contract.employee_id.id)])
                for lm in lmaternidad_all.leave_id:
                    leave_days_total = lm.number_of_days
                    leave_hours_total = lm.number_of_days * contract.resource_calendar_id.hours_per_day
                    amount_license_total = lm.amount_license
                    leave_lmaternidad = self.env['hr.work.entry'].search([("date_start", ">=", self.date_from),
                                                                       ("date_stop", "<=", self.date_to),
                                                                       ("leave_id", "=", lm.id),
                                                                       ])
                    leave_lmaternidad_hours = 0
                    for s in leave_lmaternidad:
                        leave_lmaternidad_hours += s.duration

                    leave_lmaternidad_days = leave_lmaternidad_hours / contract.resource_calendar_id.hours_per_day

                    if leave_lmaternidad_days > 15 and self.date_to.day == 31:
                        leave_lmaternidad_days = leave_lmaternidad_days - 1
                        leave_lmaternidad_hours = leave_lmaternidad_hours - contract.resource_calendar_id.hours_per_day

                    work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'LICENCIAMATERNIDADS')],limit=1)
                    leave_lm = {
                        'sequence': work_entry_type.sequence,
                        'work_entry_type_id': work_entry_type.id,
                        'name': work_entry_type.code,
                        'number_of_days': leave_lmaternidad_days,
                        'number_of_hours': leave_lmaternidad_hours,
                        'number_of_days_total': leave_days_total,
                        'number_of_hours_total': leave_hours_total,
                        'amount': amount_license_total,
                    }
                    res.append(leave_lm)

                    # Dias Licencia pareternidad

                    lpaternidad_all = self.env['hr.work.entry'].search([("date_start", ">=", self.date_from),
                                                                        ("date_stop", "<=", self.date_to),
                                                                        ("work_entry_type_id.code", "=",
                                                                         'LICENCIAPATERNIDAD'),
                                                                        ("employee_id", "=",
                                                                         contract.employee_id.id)])
                    for lp in lpaternidad_all.leave_id:
                        leave_days_total = lp.number_of_days
                        leave_hours_total = lp.number_of_days * contract.resource_calendar_id.hours_per_day
                        amount_license_total = lp.amount_license
                        leave_lpaternidad = self.env['hr.work.entry'].search([("date_start", ">=", self.date_from),
                                                                              ("date_stop", "<=", self.date_to),
                                                                              ("leave_id", "=", lm.id),
                                                                              ])
                        leave_lpaternidad_hours = 0
                        for s in leave_lpaternidad:
                            leave_lpaternidad_hours += s.duration

                        leave_lpaternidad_days = leave_lpaternidad_hours / contract.resource_calendar_id.hours_per_day

                        if leave_lpaternidad_days > 15 and self.date_to.day == 31:
                            leave_lpaternidad_days = leave_lpaternidad_days - 1
                            leave_lpaternidad_hours = leave_lpaternidad_hours - contract.resource_calendar_id.hours_per_day

                        work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'LICENCIAPATERNIDADS')],
                                                                                limit=1)
                        leave_lp = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': leave_lpaternidad_days,
                            'number_of_hours': leave_lpaternidad_hours,
                            'number_of_days_total': leave_days_total,
                            'number_of_hours_total': leave_hours_total,
                            'amount': amount_license_total,
                        }
                        res.append(leave_lp)

                # Horas Extras (# horas y valor x hora)
                horas_extras = self.get_inputs_hora_extra(contract, self.date_from, self.date_to)
                if horas_extras:
                    extradiurna_amount = 0
                    extradiurna_hours = 0
                    extradiurnafestivo_amount = 0
                    extradiurnafestivo_hours = 0
                    extranocturna_amount = 0
                    extranocturna_hours = 0
                    extranocturnafestivo_amount = 0
                    extranocturnafestivo_hours = 0
                    recargonocturno_amount = 0
                    recargonocturno_hours = 0
                    recargodiurnofestivo_amounth = 0
                    recargodiurnofestivo_hours = 0
                    recargonocturnofestivo_amount = 0
                    recargonocturnofestivo_hours = 0
                    for hora in horas_extras:
                        if hora[1] == 'EXTRADIURNA':
                            extradiurna_amount = extradiurna_amount + hora[4]
                            extradiurna_hours = extradiurna_hours + hora[5]
                        if hora[1] == 'EXTRADIURNAFESTIVO':
                            extradiurnafestivo_amount = extradiurnafestivo_amount + hora[4]
                            extradiurnafestivo_hours = extradiurnafestivo_hours + hora[5]
                        if hora[1] == 'EXTRANOCTURNA':
                            extranocturna_amount = extranocturna_amount + hora[4]
                            extranocturna_hours = extranocturna_hours + hora[5]
                        if hora[1] == 'EXTRANOCTURNAFESTIVO':
                            extranocturnafestivo_amount = extranocturnafestivo_amount + hora[4]
                            extranocturnafestivo_hours = extranocturnafestivo_hours + hora[5]
                        if hora[1] == 'RECARGONOCTURNO':
                            recargonocturno_amount = recargonocturno_amount + hora[4]
                            recargonocturno_hours = recargonocturno_hours + hora[5]
                        if hora[1] == 'RECARGODIURNOFESTIVO':
                            recargodiurnofestivo_amounth = recargodiurnofestivo_amounth + hora[4]
                            recargodiurnofestivo_hours = recargodiurnofestivo_hours + hora[5]
                        if hora[1] == 'RECARGONOCTURNOFESTIVO':
                            recargonocturnofestivo_amount = recargonocturnofestivo_amount + hora[4]
                            recargonocturnofestivo_hours = recargonocturnofestivo_hours + hora[5]

                    if not extradiurna_amount == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'EXTRADIURNA')],
                                                                                limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': extradiurna_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': extradiurna_hours,
                            'number_of_days_total': extradiurna_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': extradiurna_hours,
                            'amount': extradiurna_amount,
                        }
                        res.append(hours_e)
                    if not extradiurnafestivo_hours == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search(
                            [("code", "=", 'EXTRADIURNAFESTIVO')], limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': extradiurnafestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': extradiurnafestivo_hours,
                            'number_of_days_total': extradiurnafestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': extradiurnafestivo_hours,
                            'amount': extradiurnafestivo_amount,
                        }
                        res.append(hours_e)
                    if not extranocturna_hours == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'EXTRANOCTURNA')],
                                                                                limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': extranocturna_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': extranocturna_hours,
                            'number_of_days_total': extranocturna_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': extranocturna_hours,
                            'amount': extranocturna_amount,
                        }
                        res.append(hours_e)
                    if not extranocturnafestivo_hours == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search(
                            [("code", "=", 'EXTRANOCTURNAFESTIVO')], limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': extranocturnafestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': extranocturnafestivo_hours,
                            'number_of_days_total': extranocturnafestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': extranocturnafestivo_hours,
                            'amount': extranocturnafestivo_amount,
                        }
                        res.append(hours_e)
                    if not recargonocturno_hours == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'RECARGONOCTURNO')],
                                                                                limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': recargonocturno_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': recargonocturno_hours,
                            'number_of_days_total': recargonocturno_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': recargonocturno_hours,
                            'amount': recargonocturno_amount,
                        }
                        res.append(hours_e)
                    if not recargodiurnofestivo_hours == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search(
                            [("code", "=", 'RECARGODIURNOFESTIVO')], limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': recargodiurnofestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': recargodiurnofestivo_hours,
                            'number_of_days_total': recargodiurnofestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': recargodiurnofestivo_hours,
                            'amount': recargodiurnofestivo_amounth,
                        }
                        res.append(hours_e)
                    if not recargonocturnofestivo_hours == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search(
                            [("code", "=", 'RECARGONOCTURNOFESTIVO')], limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': recargonocturnofestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': recargonocturnofestivo_hours,
                            'number_of_days_total': recargonocturnofestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': recargonocturnofestivo_hours,
                            'amount': recargonocturnofestivo_amount,
                        }
                        res.append(hours_e)

            else:
                # Asistencia
                attendance_line = {
                    'sequence': 25,
                    'work_entry_type_id': 1,
                    'name': 'WORK100',
                    'number_of_days': 0,
                    'number_of_hours': 0,
                    'number_of_days_total': 0,
                    'number_of_hours_total': 0,
                    'amount': 0
                }
                res.append(attendance_line)

                # Dias totales
                work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'TOTALDAYS')], limit=1)
                attendances_total = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'name': work_entry_type.code,
                    'number_of_days': 0,
                    'number_of_hours': 0,
                    'number_of_days_total': 0,
                    'number_of_hours_total': 0,
                    'amount': 0
                }
                res.append(attendances_total)

                # Dias anuales trabajados
                date_init_year = date(self.date_from.year, 1, 1)
                date_to = self.date_to
                if contract.date_start <= date_init_year:
                    date_init = date_init_year
                else:
                    date_init = contract.date_start
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_year_days = days360(date_init, date_to) + 1
                suspensions_day = self.get_suspensions_day(contract, date_init, date_to)
                total_year_days = total_year_days - suspensions_day
                total_year_hours = total_year_days * contract.resource_calendar_id.hours_per_day

                work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'TOTALDAYSYEARS')], limit=1)
                attendances_year_total = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'name': work_entry_type.code,
                    'number_of_days': total_year_days,
                    'number_of_hours': total_year_hours,
                    'number_of_days_total': total_year_days,
                    'number_of_hours_total': total_year_hours,
                    'amount': 0,
                }
                res.append(attendances_year_total)

                # Dias semestrales trabajados

                if self.date_from.month <= 6 and self.date_from.day <= 31:
                    date_init_year = date(self.date_from.year, 1, 1)

                elif self.date_from.month <= 12 and self.date_from.day <= 31:
                    date_init_year = date(self.date_from.year, 7, 1)

                date_to = self.date_to
                if contract.date_start <= date_init_year:
                    date_init = date_init_year
                else:
                    date_init = contract.date_start
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_year_days = days360(date_init, date_to) + 1
                suspensions_day = self.get_suspensions_day(contract, date_init, date_to)
                total_year_days = total_year_days - suspensions_day
                total_year_hours = total_year_days * contract.resource_calendar_id.hours_per_day
                work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'TOTALDAYS6M')], limit=1)
                attendances_year_total = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'name': work_entry_type.code,
                    'number_of_days': total_year_days,
                    'number_of_hours': total_year_hours,
                    'number_of_days_total': total_year_days,
                    'number_of_hours_total': total_year_hours,
                    'amount': 0,
                }
                res.append(attendances_year_total)

                # Días trabajados desde inicio de contrato
                date_to = self.date_to
                date_init = contract.date_start
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_year_days = days360(date_init, date_to) + 1
                suspensions_day = self.get_suspensions_day(contract, date_init, date_to)
                total_year_days = total_year_days - suspensions_day
                total_year_hours = total_year_days * contract.resource_calendar_id.hours_per_day
                work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'TOTALDAYSCONTRACT')], limit=1)
                attendances_yearc_total = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'name': work_entry_type.code,
                    'number_of_days': total_year_days,
                    'number_of_hours': total_year_hours,
                    'number_of_days_total': total_year_days,
                    'number_of_hours_total': total_year_hours,
                    'amount': 0,
                }
                res.append(attendances_yearc_total)

                # Horas Extras (# horas y valor x hora)
                horas_extras = self.get_inputs_hora_extra(contract, self.date_from, self.date_to)
                if horas_extras:
                    extradiurna_amount = 0
                    extradiurna_hours = 0
                    extradiurnafestivo_amount = 0
                    extradiurnafestivo_hours = 0
                    extranocturna_amount = 0
                    extranocturna_hours = 0
                    extranocturnafestivo_amount = 0
                    extranocturnafestivo_hours = 0
                    recargonocturno_amount = 0
                    recargonocturno_hours = 0
                    recargodiurnofestivo_amounth = 0
                    recargodiurnofestivo_hours = 0
                    recargonocturnofestivo_amount = 0
                    recargonocturnofestivo_hours = 0
                    for hora in horas_extras:
                        if hora[1] == 'EXTRADIURNA':
                            extradiurna_amount = extradiurna_amount + hora[4]
                            extradiurna_hours = extradiurna_hours + hora[5]
                        if hora[1] == 'EXTRADIURNAFESTIVO':
                            extradiurnafestivo_amount = extradiurnafestivo_amount + hora[4]
                            extradiurnafestivo_hours = extradiurnafestivo_hours + hora[5]
                        if hora[1] == 'EXTRANOCTURNA':
                            extranocturna_amount = extranocturna_amount + hora[4]
                            extranocturna_hours = extranocturna_hours + hora[5]
                        if hora[1] == 'EXTRANOCTURNAFESTIVO':
                            extranocturnafestivo_amount = extranocturnafestivo_amount + hora[4]
                            extranocturnafestivo_hours = extranocturnafestivo_hours + hora[5]
                        if hora[1] == 'RECARGONOCTURNO':
                            recargonocturno_amount = recargonocturno_amount + hora[4]
                            recargonocturno_hours = recargonocturno_hours + hora[5]
                        if hora[1] == 'RECARGODIURNOFESTIVO':
                            recargodiurnofestivo_amounth = recargodiurnofestivo_amounth + hora[4]
                            recargodiurnofestivo_hours = recargodiurnofestivo_hours + hora[5]
                        if hora[1] == 'RECARGONOCTURNOFESTIVO':
                            recargonocturnofestivo_amount = recargonocturnofestivo_amount + hora[4]
                            recargonocturnofestivo_hours = recargonocturnofestivo_hours + hora[5]

                    if not extradiurna_amount == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'EXTRADIURNA')],
                                                                                limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': extradiurna_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': extradiurna_hours,
                            'number_of_days_total': extradiurna_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': extradiurna_hours,
                            'amount': extradiurna_amount,
                        }
                        res.append(hours_e)
                    if not extradiurnafestivo_hours == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search(
                            [("code", "=", 'EXTRADIURNAFESTIVO')], limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': extradiurnafestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': extradiurnafestivo_hours,
                            'number_of_days_total': extradiurnafestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': extradiurnafestivo_hours,
                            'amount': extradiurnafestivo_amount,
                        }
                        res.append(hours_e)
                    if not extranocturna_hours == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'EXTRANOCTURNA')],
                                                                                limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': extranocturna_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': extranocturna_hours,
                            'number_of_days_total': extranocturna_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': extranocturna_hours,
                            'amount': extranocturna_amount,
                        }
                        res.append(hours_e)
                    if not extranocturnafestivo_hours == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search(
                            [("code", "=", 'EXTRANOCTURNAFESTIVO')], limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': extranocturnafestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': extranocturnafestivo_hours,
                            'number_of_days_total': extranocturnafestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': extranocturnafestivo_hours,
                            'amount': extranocturnafestivo_amount,
                        }
                        res.append(hours_e)
                    if not recargonocturno_hours == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'RECARGONOCTURNO')],
                                                                                limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': recargonocturno_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': recargonocturno_hours,
                            'number_of_days_total': recargonocturno_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': recargonocturno_hours,
                            'amount': recargonocturno_amount,
                        }
                        res.append(hours_e)
                    if not recargodiurnofestivo_hours == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search(
                            [("code", "=", 'RECARGODIURNOFESTIVO')], limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': recargodiurnofestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': recargodiurnofestivo_hours,
                            'number_of_days_total': recargodiurnofestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': recargodiurnofestivo_hours,
                            'amount': recargodiurnofestivo_amounth,
                        }
                        res.append(hours_e)
                    if not recargonocturnofestivo_hours == 0:
                        work_entry_type = self.env['hr.work.entry.type'].search(
                            [("code", "=", 'RECARGONOCTURNOFESTIVO')], limit=1)
                        hours_e = {
                            'sequence': work_entry_type.sequence,
                            'work_entry_type_id': work_entry_type.id,
                            'name': work_entry_type.code,
                            'number_of_days': recargonocturnofestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours': recargonocturnofestivo_hours,
                            'number_of_days_total': recargonocturnofestivo_hours / contract.resource_calendar_id.hours_per_day,
                            'number_of_hours_total': recargonocturnofestivo_hours,
                            'amount': recargonocturnofestivo_amount,
                        }
                        res.append(hours_e)



        return res

    def _get_payslip_lines(self):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = localdict['categories'].dict.get(category.code, 0) + amount
            return localdict

        self.ensure_one()
        result = {}
        rules_dict = {}
        worked_days_dict = {line.code: line for line in self.worked_days_line_ids if line.code}
        # Se modifico inputs_dict que tomaras otros campos de hr.payslip.input
        inputs_dict = {line.code_input: line for line in self.input_line_ids if line.code_input}

        employee = self.employee_id
        contract = self.contract_id

        localdict = {
            **self._get_base_local_dict(),
            **{
                'categories': BrowsableObject(employee.id, {}, self.env),
                'rules': BrowsableObject(employee.id, rules_dict, self.env),
                'payslip': Payslips(employee.id, self, self.env),
                'worked_days': WorkedDays(employee.id, worked_days_dict, self.env),
                'inputs': InputLine(employee.id, inputs_dict, self.env),
                'employee': employee,
                'contract': contract
            }
        }
        for rule in sorted(self.struct_id.rule_ids, key=lambda x: x.sequence):
            localdict.update({
                'result': None,
                'result_qty': 1.0,
                'result_rate': 100})
            if rule._satisfy_condition(localdict):
                amount, qty, rate = rule._compute_rule(localdict)
                # check if there is already a rule computed with that code
                previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                # set/overwrite the amount computed for this rule in the localdict
                tot_rule = amount * qty * rate / 100.0
                localdict[rule.code] = tot_rule
                rules_dict[rule.code] = rule
                # sum the amount for its salary category
                localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                # create/overwrite the rule in the temporary results
                result[rule.code] = {
                    'sequence': rule.sequence,
                    'code': rule.code,
                    'name': rule.name,
                    'note': rule.note,
                    'salary_rule_id': rule.id,
                    'contract_id': contract.id,
                    'employee_id': employee.id,
                    'amount': amount,
                    'quantity': qty,
                    'rate': rate,
                    'slip_id': self.id,
                }
        return result.values()