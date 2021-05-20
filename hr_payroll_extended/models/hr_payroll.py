<<<<<<< HEAD
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
        self._cr.execute(''' SELECT i.name, i.code, h.total_money, i.id FROM hr_extras h
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

    def get_inputs_loans_12month_before(self, contract_id, date_from, date_to):
        lm12_date_ini = date_to - relativedelta(months=12)

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

    def get_inputs_loans_fijos(self, contract_id):
        self._cr.execute(''' SELECT i.name, i.code, h.loan_amount
                                FROM hr_loan h
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approve'
                                AND h.loan_fijo IS True
                                ORDER BY i.code ''',(contract_id.id,))
        loans_fijos_ids = self._cr.fetchall()
        return loans_fijos_ids

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = []

        self._cr.execute(''' DELETE FROM hr_payslip_input WHERE payslip_id=%s ''', (self.id,))
        for contract in contracts:
            horas_extras = self.get_inputs_hora_extra(contract, date_from, date_to)
            if horas_extras:
                amounth25 = 0
                inputh25_type_id = 0
                amounth35 = 0
                inputh35_type_id = 0
                amounth75 = 0
                inputh75_type_id = 0
                amounthf75 = 0
                inputhf75_type_id = 0
                amounth110 = 0
                inputh110_type_id = 0
                for hora in horas_extras:
                    if hora[1] == 'EXTRADIURNA':
                        amounth25 = amounth25 + hora[2]
                        inputh25_type_id = hora[3]
                        nameh25 = hora[0]
                        codeh25 = hora[1]
                    if hora[1] == 'RECARGONOCTURNO':
                        amounth35 = amounth35 + hora[2]
                        inputh35_type_id = hora[3]
                        nameh35 = hora[0]
                        codeh35 = hora[1]
                    if hora[1] == 'EXTRANOCTURNA':
                        amounth75 = amounth75 + hora[2]
                        inputh75_type_id = hora[3]
                        nameh75 = hora[0]
                        codeh75 = hora[1]
                    if hora[1] == 'RECARGODIURNOFESTIVO':
                        amounthf75 = amounthf75 + hora[2]
                        inputhf75_type_id = hora[3]
                        namehf75 = hora[0]
                        codehf75 = hora[1]
                    if hora[1] == 'RECARGONOCTURNOFESTIVO':
                        amounth110 = amounth110 + hora[2]
                        inputh110_type_id = hora[3]
                        nameh110 = hora[0]
                        codeh110 = hora[1]
                if not amounth25 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amounth25,
                        "payslip_id": self.id,
                        "input_type_id": inputh25_type_id,
                        "name_input": nameh25,
                        "code_input": codeh25,
                    })
                if not amounth35 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amounth35,
                        "payslip_id": self.id,
                        "input_type_id": inputh35_type_id,
                        "name_input": nameh35,
                        "code_input": codeh35,
                    })
                if not amounth75 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amounth75,
                        "payslip_id": self.id,
                        "input_type_id": inputh75_type_id,
                        "name_input": nameh75,
                        "code_input": codeh75,
                    })
                if not amounthf75 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amounthf75,
                        "payslip_id": self.id,
                        "input_type_id": inputhf75_type_id,
                        "name_input": namehf75,
                        "code_input": codehf75,
                    })
                if not amounth110 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amounth110,
                        "payslip_id": self.id,
                        "input_type_id": inputh110_type_id,
                        "name_input": nameh110,
                        "code_input": codeh110,
                    })
            hora_extra_month_before = self.get_inputs_hora_extra_month_before(contract, date_from, date_to)
            if hora_extra_month_before:
                amounth25 = 0
                inputh25_type_id = 0
                amounth35 = 0
                inputh35_type_id = 0
                amounth75 = 0
                inputh75_type_id = 0
                amounthf75 = 0
                inputhf75_type_id = 0
                amounth110 = 0
                inputh110_type_id = 0
                for hora in horas_extras:
                    if hora[1] == 'EXTRADIURNA':
                        amounth25 = amounth25 + hora[2]
                        inputh25_type_id = hora[3]
                        nameh25 = hora[0]
                        codeh25 = hora[1]
                    if hora[1] == 'RECARGONOCTURNO':
                        amounth35 = amounth35 + hora[2]
                        inputh35_type_id = hora[3]
                        nameh35 = hora[0]
                        codeh35 = hora[1]
                    if hora[1] == 'EXTRANOCTURNA':
                        amounth75 = amounth75 + hora[2]
                        inputh75_type_id = hora[3]
                        nameh75 = hora[0]
                        codeh75 = hora[1]
                    if hora[1] == 'RECARGODIURNOFESTIVO':
                        amounthf75 = amounthf75 + hora[2]
                        inputhf75_type_id = hora[3]
                        namehf75 = hora[0]
                        codehf75 = hora[1]
                    if hora[1] == 'RECARGONOCTURNOFESTIVO':
                        amounth110 = amounth110 + hora[2]
                        inputh110_type_id = hora[3]
                        nameh110 = hora[0]
                        codeh110 = hora[1]
                if not amounth25 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amounth25,
                        "payslip_id": self.id,
                        "input_type_id": inputh25_type_id,
                        "code_input": 'EXTRADIURNA_ANT30',
                        "name_input": 'Horas Extra Diurna (25%) Mes Anterior',
                    })
                if not amounth35 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amounth35,
                        "payslip_id": self.id,
                        "input_type_id": inputh35_type_id,
                        "code_input": 'RECARGONOCTURNO_ANT30',
                        "name_input": 'Horas Recargo Nocturno (35%) Mes Anterior',
                    })
                if not amounth75 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amounth75,
                        "payslip_id": self.id,
                        "input_type_id": inputh75_type_id,
                        "code_input": 'EXTRANOCTURNA_ANT30',
                        "name_input": 'Horas Extra Nocturna (75%) Mes Anterior',
                    })
                if not amounthf75 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amounthf75,
                        "payslip_id": self.id,
                        "input_type_id": inputhf75_type_id,
                        "code_input": 'RECARGODIURNOFESTIVO_ANT30',
                        "name_input": 'Horas Recargo Diurno Festivo (75%) Mes Anterior',
                    })
                if not amounth110 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amounth110,
                        "payslip_id": self.id,
                        "input_type_id": inputh110_type_id,
                        "code_input": 'RECARGONOCTURNOFESTIVO_ANT30',
                        "name_input": 'Horas Recargo Nocturno Festivo (110%) Mes Anterior',
                    })
            horas_extras_12month_before = self.get_inputs_hora_extra_12month_before(contract, date_from, date_to)
            if horas_extras_12month_before:
                hm12_date_ini = date_to - relativedelta(months=12)
                hm12_date_ini = hm12_date_ini + relativedelta(days=1)
                if contract.date_start <= hm12_date_ini:
                    hm12_date_init = hm12_date_ini
                else:
                    hm12_date_init = contract.date_start
                #total_days12y = days_between(hm12_date_init, date_to)
                total_days12y = days360(hm12_date_init, date_to) + 1
                counth25 = 0
                amounth25 = 0
                inputh25_type_id = 0
                counth35 = 0
                amounth35 = 0
                inputh35_type_id = 0
                counth75 = 0
                amounth75 = 0
                inputh75_type_id = 0
                counthf75 = 0
                amounthf75 = 0
                inputhf75_type_id = 0
                counth110 = 0
                amounth110 = 0
                inputh110_type_id = 0
                for hora in horas_extras_12month_before:
                    if hora[1] == 'RECARGONOCTURNO':
                        counth35 = counth35 + 1
                        amounth35 = amounth35 + hora[2]
                        inputh35_type_id = hora[3]
                        nameh35 = hora[0]
                        codeh35 = hora[1]
                    if hora[1] == 'RECARGODIURNOFESTIVO':
                        counthf75 = counthf75 + 1
                        amounthf75 = amounthf75 + hora[2]
                        inputhf75_type_id = hora[3]
                        namehf75 = hora[0]
                        codehf75 = hora[1]
                    if hora[1] == 'RECARGONOCTURNOFESTIVO':
                        counth110 = counth110 + 1
                        amounth110 = amounth110 + hora[2]
                        inputh110_type_id = hora[3]
                        nameh110 = hora[0]
                        codeh110 = hora[1]

                    if hora[1] == 'EXTRADIURNA':
                        counth25 = counth25 + 1
                        amounth25 = amounth25 + hora[2]
                        inputh25_type_id = hora[3]
                        nameh25 = hora[0]
                        codeh25 = hora[1]
                    if hora[1] == 'EXTRANOCTURNA':
                        counth75 = counth75 + 1
                        amounth75 = amounth75 + hora[2]
                        inputh75_type_id = hora[3]
                        nameh75 = hora[0]
                        codeh75 = hora[1]

                if not amounth25 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amounth25/total_days12y)*30,
                        "payslip_id": self.id,
                        "input_type_id": inputh25_type_id,
                        "code_input": 'EXTRADIURNA_PYEARS',
                        "name_input": 'Horas Extra Diurna (25%) Promedio 12M atras',
                    })
                if not amounth35 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amounth35/total_days12y)*30,
                        "payslip_id": self.id,
                        "input_type_id": inputh35_type_id,
                        "code_input": 'RECARGONOCTURNO_PYEARS',
                        "name_input": 'Horas Recargo Nocturno (35%) Promedio 12M atras',
                    })
                if not amounth75 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amounth75/total_days12y)*30,
                        "payslip_id": self.id,
                        "input_type_id": inputh75_type_id,
                        "code_input": 'EXTRANOCTURNA_PYEARS',
                        "name_input": 'Horas Extra Nocturna (75%) Promedio 12M atras',
                    })
                if not amounthf75 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amounthf75/total_days12y)*30,
                        "payslip_id": self.id,
                        "input_type_id": inputhf75_type_id,
                        "code_input": 'RECARGODIURNOFESTIVO_PYEARS',
                        "name_input": 'Horas Recargo Diurno Festivo (75%) Promedio 12M atras',
                    })
                if not amounth110 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amounth110/total_days12y)*30,
                        "payslip_id": self.id,
                        "input_type_id": inputh110_type_id,
                        "code_input": 'RECARGONOCTURNOFESTIVO_PYEARS',
                        "name_input": 'Horas Recargo Nocturno Festivo (110%) Promedio 12M atras',
                    })
            hora_extra_year_now = self.get_inputs_hora_extra_year_now(contract, date_from, date_to)
            if hora_extra_year_now:
                hdate_init_year = date(date_from.year, 1, 1)
                if contract.date_start <= hdate_init_year:
                    hdate_init = hdate_init_year
                else:
                    hdate_init = contract.date_start
                #total_days = days_between(hdate_init, date_to)
                total_days = days360(hdate_init, date_to)
                counth25 = 0
                amounth25 = 0
                inputh25_type_id = 0
                counth35 = 0
                amounth35 = 0
                inputh35_type_id = 0
                counth75 = 0
                amounth75 = 0
                inputh75_type_id = 0
                counthf75 = 0
                amounthf75 = 0
                inputhf75_type_id = 0
                counth110 = 0
                amounth110 = 0
                inputh110_type_id = 0
                for hora in hora_extra_year_now:
                    if hora[1] == 'RECARGONOCTURNO':
                        counth35 = counth35 + 1
                        amounth35 = amounth35 + hora[2]
                        inputh35_type_id = hora[3]
                        nameh35 = hora[0]
                        codeh35 = hora[1]
                    if hora[1] == 'RECARGODIURNOFESTIVO':
                        counthf75 = counthf75 + 1
                        amounthf75 = amounthf75 + hora[2]
                        inputhf75_type_id = hora[3]
                        namehf75 = hora[0]
                        codehf75 = hora[1]
                    if hora[1] == 'RECARGONOCTURNOFESTIVO':
                        counth110 = counth110 + 1
                        amounth110 = amounth110 + hora[2]
                        inputh110_type_id = hora[3]
                        nameh110 = hora[0]
                        codeh110 = hora[1]
                    if hora[1] == 'EXTRADIURNA':
                        counth25 = counth25 + 1
                        amounth25 = amounth25 + hora[2]
                        inputh25_type_id = hora[3]
                        nameh25 = hora[0]
                        codeh25 = hora[1]
                    if hora[1] == 'EXTRANOCTURNA':
                        counth75 = counth75 + 1
                        amounth75 = amounth75 + hora[2]
                        inputh75_type_id = hora[3]
                        nameh75 = hora[0]
                        codeh75 = hora[1]
                if not amounth25 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amounth25/total_days)*30,
                        "payslip_id": self.id,
                        "input_type_id": inputh25_type_id,
                        "code_input": 'EXTRADIURNA_YEARS_NOW',
                        "name_input": 'Horas Extra Diurna (25%) Promedio Anual',
                    })
                if not amounth35 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amounth35/total_days)*30,
                        "payslip_id": self.id,
                        "input_type_id": inputh35_type_id,
                        "code_input": 'RECARGONOCTURNO_YEARS_NOW',
                        "name_input": 'Horas Recargo Nocturno (35%) Promedio Anual',
                    })
                if not amounth75 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amounth75/total_days)*30,
                        "payslip_id": self.id,
                        "input_type_id": inputh75_type_id,
                        "code_input": 'EXTRANOCTURNA_YEARS_NOW',
                        "name_input": 'Horas Extra Nocturna (75%) Promedio Anual',
                    })
                if not amounthf75 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amounthf75/total_days)*30,
                        "payslip_id": self.id,
                        "input_type_id": inputhf75_type_id,
                        "code_input": 'RECARGODIURNOFESTIVO_YEARS_NOW',
                        "name_input": 'Horas Recargo Diurno Festivo (75%) Promedio Anual',
                    })
                if not amounth110 == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amounth110/total_days)*30,
                        "payslip_id": self.id,
                        "input_type_id": inputh110_type_id,
                        "code_input": 'RECARGONOCTURNOFESTIVO_YEARS_NOW',
                        "name_input": 'Horas Recargo Nocturno Festivo (110%) Promedio Anual',
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
            loans_ids = self.get_inputs_loans(contract, date_from, date_to)
            if loans_ids:
                amountb = 0
                inputb_type_id = 0
                amountd = 0
                inputd_type_id = 0
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
            loans_month_now_ids = self.get_inputs_loans_month_now(contract, date_from, date_to)
            if loans_month_now_ids and date_from.day == 16:
                amountbn = 0
                inputbn_type_id = 0
                amountdn = 0
                inputdn_type_id = 0
                for loans in loans_month_now_ids:
                    if loans[1] == 'BONIFICACION':
                        amountbn = amountbn + loans[2]
                        inputbn_type_id = loans[3]
                    if loans[1] == 'DESCUENTOS':
                        amountdn = amountdn + loans[2]
                        inputdn_type_id = loans[3]
                if not amountbn == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amountbn,
                        "payslip_id": self.id,
                        "input_type_id": inputbn_type_id,
                        "code_input": 'BONIFICACION_NOW30',
                        "name_input": 'Bonificación Mes Actual',
                    })
                """
                if not amountdn == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amountdn,
                        "payslip_id": self.id,
                        "input_type_id": inputdn_type_id,
                        "code_input": 'DESCUENTO_NOW30',
                        "name_input": 'Descuento Mes Actual',
                    })
                """
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
            loans_month_before_ids = self.get_inputs_loans_month_before(contract, date_from, date_to)
            if loans_month_before_ids:
                amountb = 0
                inputb_type_id = 0
                amountd = 0
                inputd_type_id = 0
                for loans in loans_month_before_ids:
                    if loans[1] == 'BONIFICACION':
                       amountb = amountb + loans[2]
                       inputb_type_id = loans[3]
                    if loans[1] == 'DESCUENTOS':
                       amountd = amountd + loans[2]
                       inputd_type_id = loans[3]
                if not amountb == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amountb,
                        "payslip_id": self.id,
                        "input_type_id": inputb_type_id,
                        "code_input": 'BONIFICACION_ANT30',
                        "name_input": 'Bonificación Mes Anterior',
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
            inputs_loans_12month_before = self.get_inputs_loans_12month_before(contract, date_from, date_to)
            if inputs_loans_12month_before:
                lm12_date_ini = date_to - relativedelta(months=12)
                if contract.date_start <= lm12_date_ini:
                    lm12_date_init = lm12_date_ini
                else:
                    lm12_date_init = contract.date_start
                #total_dayl12 = days_between(lm12_date_init, date_to)
                total_dayl12 = days360(lm12_date_init, date_to)
                countb = 0
                amountb = 0
                inputb_type_id = 0
                for loans in inputs_loans_12month_before:
                    if loans[1] == 'BONIFICACION':
                        countb = countb + 1
                        amountb = amountb + loans[2]
                        inputb_type_id = loans[3]
                if not amountb == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amountb/total_dayl12)*30,
                        "payslip_id": self.id,
                        "input_type_id": inputb_type_id,
                        "code_input": 'BONIFICACION_PYEARS',
                        "name_input": 'Bonificación Promedio (12M atras)',
                    })
            loans_year_now = self.get_inputs_loans_year_now(contract, date_from, date_to)
            if loans_year_now:
                ldate_init_year = date(date_from.year, 1, 1)
                if contract.date_start <= ldate_init_year:
                    ldate_init = ldate_init_year
                else:
                    ldate_init = contract.date_start
                #ltotal_days = days_between(ldate_init, date_to)
                ltotal_days = days360(ldate_init, date_to)
                countb = 0
                amountb = 0
                inputb_type_id = 0
                for loans in loans_year_now:
                    if loans[1] == 'BONIFICACION':
                        countb = countb + 1
                        amountb = amountb + loans[2]
                        inputb_type_id = loans[3]
                if not amountb == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": (amountb/ltotal_days)*30,
                        "payslip_id": self.id,
                        "input_type_id": inputb_type_id,
                        "code_input": 'BONIFICACION_YEARS_NOW',
                        "name_input": 'Bonificación Promedio Anual',
                    })
            amount_transport_subsidy_pyear = self.get_amount_transport_subsidy_year(contract, date_from, date_to)
            if amount_transport_subsidy_pyear and amount_transport_subsidy_pyear > 0 :
                code_aux_transp = self.env['hr.payslip.input.type'].search([("code", "=", 'AUX_TRANSPORTE_PYEARS')], limit=1).id
                self.env['hr.payslip.input'].create({
                    "sequence": 1,
                    "amount": amount_transport_subsidy_pyear,
                    "payslip_id": self.id,
                    "input_type_id": code_aux_transp if code_aux_transp else inputb_type_id,
                    "code_input": 'AUX_TRANSPORTE_PYEARS',
                    "name_input": 'Auxilio de Transporte Promedio Anual',
                })
            if contract.retention_method == 'M1':
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
            else:
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
            total_hours = total_days*contract.resource_calendar_id.hours_per_day
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

            # Dias anuales trabajados
            date_init_year = date(self.date_from.year, 1, 1)
            if contract.date_start <= date_init_year:
                date_init = date_init_year
            else:
                date_init = contract.date_start
            total_year_days = days360(date_init, self.date_to)
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

            # Total ausencias por enfermedad
            absence_rate_2D = self.env['hr.salary.rule'].search([("code", "=", 'P_AUSENCIAS_2D')], limit=1).amount_fix
            absence_rate_90D = self.env['hr.salary.rule'].search([("code", "=", 'P_AUSENCIAS_90D')], limit=1).amount_fix
            absence_rate_M91D = self.env['hr.salary.rule'].search([("code", "=", 'P_AUSENCIAS_M91D')], limit=1).amount_fix
            work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'LEAVE110')], limit=1)
            leave_sickness_amount_total = 0
            leave_sickness_days_total = 0
            leave_sickness_hours_total = 0
            leave_days_t = 0
            leave_hours_t = 0

            loans_month_before_ids = self.get_inputs_loans_month_before(contract, self.date_from, self.date_to)
            boni_month_before = 0
            if loans_month_before_ids:
                for loans in loans_month_before_ids:
                    if loans[1] == 'BONIFICACION':
                        boni_month_before += loans[2]

            leave_sickness_all = self.env['hr.work.entry'].search([("date_start", ">=", self.date_from),
                                                                  ("date_stop", "<=", self.date_to),
                                                                  ("work_entry_type_id", "=", work_entry_type.id),
                                                                  ("employee_id", "=", contract.employee_id.id)])
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

                if leave_sickness_days >= 1 and leave_sickness_days <= 2:
                    leave_sickness_amount = round(((((paid_amount + boni_month_before)/30)*leave_sickness_days)*absence_rate_2D)/100, -2)
                elif leave_sickness_days >= 3 and leave_sickness_days <= 90:
                    leave_sickness_amount = round(((((paid_amount + boni_month_before)/30)*leave_sickness_days)*absence_rate_90D)/100, -2)
                elif leave_sickness_days >= 91:
                    leave_sickness_amount = round(((((paid_amount + boni_month_before)/30)*leave_sickness_days)*absence_rate_M91D)/100, -2)
                else:
                    leave_sickness_amount = 0

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
            if not  leave_sickness_days_total == 0:
                res.append(totalae)
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
=======
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

           
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'


    type_payslip_id = fields.Many2one('hr.type.payslip', string="Type")


    def actualizar_entradas(self):
        res = self._onchange_employee()
        inputs = self.get_inputs(self.contract_id, self.date_from, self.date_to)
        return True


    def get_inputs_hora_extra(self, contract_id, date_from, date_to):
        self._cr.execute(''' SELECT i.name, i.code, h.amount, i.id FROM hr_extras h
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approved'
                                AND h.date BETWEEN %s AND %s
                                ORDER BY i.code''',(contract_id.id, date_from, date_to))
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

    def get_inputs_loans_fijos(self, contract_id):
        self._cr.execute(''' SELECT i.name, i.code, h.loan_amount
                                FROM hr_loan h
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s AND h.state='approve'
                                AND h.loan_fijo IS True
                                ORDER BY i.code ''',(contract_id.id,))
        loans_fijos_ids = self._cr.fetchall()
        return loans_fijos_ids


    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = []

        self._cr.execute(''' DELETE FROM hr_payslip_input WHERE payslip_id=%s ''', (self.id,))
        for contract in contracts:
            horas_extras = self.get_inputs_hora_extra(contract, date_from, date_to)
            if horas_extras:
                for hora in horas_extras:
                    self.env['hr.payslip.input'].create({
                                "sequence": 1,
                                "amount": hora[2],
                                "payslip_id": self.id,
                                "input_type_id": hora[3],
                    })                    
            loans_ids = self.get_inputs_loans(contract, date_from, date_to)
            if loans_ids:
                for hora in loans_ids:
                    self.env['hr.payslip.input'].create({
                                "sequence": 1,
                                "amount": hora[2],
                                "payslip_id": self.id,
                                "input_type_id": hora[3],
                    })                    
            loans_fijos_ids = self.get_inputs_loans_fijos(contract)
            if loans_fijos_ids:
                for hora in loans_fijos_ids:
                    self.env['hr.payslip.input'].create({
                                "sequence": 1,
                                "amount": hora[2],
                                "payslip_id": self.id,
                                "input_type_id": hora[3],
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
            absence_rate_2D = self.env['hr.salary.rule'].search([("code", "=", 'P_AUSENCIAS_2D')], limit=1).amount_fix
            absence_rate_90D = self.env['hr.salary.rule'].search([("code", "=", 'P_AUSENCIAS_90D')], limit=1).amount_fix
            absence_rate_M91D = self.env['hr.salary.rule'].search([("code", "=", 'P_AUSENCIAS_M91D')], limit=1).amount_fix
            unpaid_work_entry_types = self.struct_id.unpaid_work_entry_type_ids.ids
            work_hours = contract._get_work_hours(self.date_from, self.date_to)
            exceed_hours = contract._get_exceed_hours(self.date_from, self.date_to)
            if exceed_hours:
                if 6 in  exceed_hours:
                    exceed_hours[11] = exceed_hours.pop(6)
                    work_hours.update(exceed_hours)
            total_hours = sum(work_hours.values()) or 1
            work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
            biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
            add_days_rounding = 0
            print ('-------444', work_hours_ordered, work_hours, total_hours)
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
                if work_entry_type_id == 6 or work_entry_type_id == 11 :
                    if day_rounded >= 3 and day_rounded < 4:
                            r_amount = (((paid_amount / 30) * absence_rate_2D) / 100) * day_rounded
                    elif day_rounded >= 4 and day_rounded <= 90:
                            r_amount = (((paid_amount / 30) * absence_rate_90D) / 100) * day_rounded
                    elif day_rounded >= 91:
                            r_amount = (((paid_amount / 30) * absence_rate_M91D) / 100) * day_rounded
                else:
                    r_amount = day_rounded * (paid_amount / 30) if is_paid else 0
                attendance_line = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type_id,
                    'name': work_entry_type.code,
                    'number_of_days': day_rounded,
                    'number_of_hours': hours,
                   #'amount': hours * paid_amount / total_hours if is_paid else 0,
                    'amount': r_amount
                }
                res.append(attendance_line)
            total_days = days_between(self.date_from, self.date_to)
            total_hours = total_days*contract.resource_calendar_id.hours_per_day
            work_entry_type = self.env['hr.work.entry.type'].search([("code", "=", 'TOTALDAYS')], limit=1)
            attendances_total = {
                'sequence': work_entry_type.sequence,
                'work_entry_type_id': work_entry_type.id,
                'name': work_entry_type.code,
                'number_of_days': total_days,
                'number_of_hours': total_hours,
                #'amount': total_hours * paid_amount / total_hours or 0,
                'amount': total_days * (paid_amount / 30) or 0,

            }
            res.append(attendances_total)
        return res


    # @api.model
    # def get_worked_day_lines(self, contracts, date_from, date_to):
    #     """
    #     @param contract: Browse record of contracts
    #     @return: returns a list of dict containing the input that should be
    #     applied for the given contract between date_from and date_to
    #     """
    #     res = []
    #     # fill only if the contract as a working schedule linked
    #     for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
    #         day_from = datetime.combine(date_from, time.min)
    #         day_to = datetime.combine(date_to, time.max)

    #         # compute leave days
    #         leaves = {}
    #         calendar = contract.resource_calendar_id
    #         tz = timezone(calendar.tz)
    #         day_leave_intervals = contract.employee_id.list_leaves(
    #             day_from, day_to, calendar=contract.resource_calendar_id
    #         )
    #         for day, hours, leave in day_leave_intervals:
    #             holiday = leave[:1].holiday_id
    #             current_leave_struct = leaves.setdefault(
    #                 holiday.holiday_status_id,
    #                 {
    #                     "name": holiday.holiday_status_id.name or _("Global Leaves"),
    #                     "sequence": 5,
    #                     "code": holiday.holiday_status_id.name or "GLOBAL",
    #                     "number_of_days": 0.0,
    #                     "number_of_hours": 0.0,
    #                     "contract_id": contract.id,
    #                 },
    #             )
    #             current_leave_struct["number_of_hours"] += hours
    #             work_hours = calendar.get_work_hours_count(
    #                 tz.localize(datetime.combine(day, time.min)),
    #                 tz.localize(datetime.combine(day, time.max)),
    #                 compute_leaves=False,
    #             )
    #             if work_hours:
    #                 current_leave_struct["number_of_days"] += hours / work_hours

    #         # compute worked days
    #         if contract.date_start >= self.date_from:
    #             day_from = datetime.combine(contract.date_start, time.min)
    #             work_data = contract.employee_id._get_work_days_data(
    #                 day_from, day_to, calendar=contract.resource_calendar_id
    #             )
    #         else:
    #             work_data = contract.employee_id._get_work_days_data(
    #                 day_from, day_to, calendar=contract.resource_calendar_id
    #             )
               
    #         if not contract.resource_calendar_id.hours_per_day:
    #             raise ValidationError(
    #                 _("Debe ingresar la cantidad de horas por dia en la Planificación de trabajo del contrato del empleado")
    #             )                
    #         total_days = days_between(date_from, date_to)
    #         total_hours = total_days*contract.resource_calendar_id.hours_per_day
    #         attendances_total = {
    #             "name": _("Total del periodo"),
    #             "sequence": 1,
    #             "code": "TOTALDAYS",
    #             "number_of_days": total_days,
    #             "number_of_hours": total_hours,
    #             "contract_id": contract.id,
    #         }            

    #         attendances = {
    #             "name": _("Normal Working Days paid at 100%"),
    #             "sequence": 1,
    #             "code": "WORK100",
    #             "number_of_days": work_data["days"],
    #             "number_of_hours": work_data["hours"],
    #             "contract_id": contract.id,
    #         }

    #         res.append(attendances_total)
    #         res.append(attendances)
    #         res.extend(leaves.values())
    #     return res        
>>>>>>> 14b5e054f2a378822e55bbb89100ad6968606a84
