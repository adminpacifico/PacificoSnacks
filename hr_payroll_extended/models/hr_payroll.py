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

    def get_inputs_loans_month_before(self, contract_id, date_from, date_to):
        date_before = self.date_from - relativedelta(months=1)
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
                        "name_input": 'Bonificación mes anterior',
                    })
                if not amountd == 0:
                    self.env['hr.payslip.input'].create({
                        "sequence": 1,
                        "amount": amountd,
                        "payslip_id": self.id,
                        "input_type_id": inputd_type_id,
                        "code_input": 'DESCUENTO_ANT30',
                        "name_input": 'Descuento mes anterior',
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
            wage_min  = self.env['hr.salary.rule'].search([("code", "=", 'SMLMV')], limit=1).amount_fix
            loans_month_before_ids = self.get_inputs_loans_month_before(contract, self.date_from, self.date_to)
            if loans_month_before_ids:
                amountb = 0
                inputb_type_id = 0
                amountd = 0
                inputd_type_id = 0
                for loans in loans_month_before_ids:
                    if loans[1] == 'BONIFICACION':
                        amountb = amountb + loans[2]
                    if loans[1] == 'DESCUENTOS':
                        amountd = amountd + loans[2]
                if not amountb == 0 and amountd == 0:
                     paid_amount_ant = paid_amount +  amountb - amountd
                else: paid_amount_ant = paid_amount
            else:
                paid_amount_ant = paid_amount
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
                # El ('work_entry_type_id', '=', 6) corresponde al tipo de entrada "Ausencias por Enfermedad", en caso de modificar el registro se debe cambiar el numero a evaluar
                # El ('work_entry_type_id', '=', 10) corresponde al tipo de entrada "Total Ausencias por Enfermedad", en caso de modificar el registro se debe cambiar el numero a evaluar
                if work_entry_type_id == 6 or work_entry_type_id == 10 :
                    if (paid_amount_ant/30) >= (wage_min / 30):
                        paid_amount_ant = (paid_amount_ant/30)
                    else:
                        paid_amount_ant = (wage_min / 30)
                    if day_rounded >= 3 and day_rounded < 4:
                            r_amount = (((paid_amount_ant) * absence_rate_2D) / 100) * day_rounded
                    elif day_rounded >= 4 and day_rounded <= 90:
                            r_amount = (((paid_amount_ant) * absence_rate_90D) / 100) * day_rounded
                    elif day_rounded >= 91:
                            r_amount = (((paid_amount_ant) * absence_rate_M91D) / 100) * day_rounded
                else:
                    r_amount = day_rounded * (paid_amount_ant / 30) if is_paid else 0

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