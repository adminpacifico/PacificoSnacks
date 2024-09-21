# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2017 CodUP (<http://codup.com>).
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero
from odoo.tools.safe_eval import safe_eval as eval
import logging

_logger = logging.getLogger(__name__)


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    empleado = fields.Boolean(string="Empleado", help="Solo si el empleado debe aparecer en el movimiento contable", default=False)
    tercero = fields.Boolean(string="Tercero", help='Dejar sin terecero si es el Empleado, o la empresa. Si selecciona este no seleccionar empleado', default=False)
    campo_contrato = fields.Char(string='Campo', help='Nonmbre del campo del tercero relacionado tomado del contrato - eps_id, pension_id, etc')


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip'

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        encontro = False
        if self.salary_rule_id.tipo_entidad_asociada:
            if self.salary_rule_id.tipo_entidad_asociada == 'arl':
                partner_id = self.slip_id.contract_id.arl_id.id
                encontro = True
            elif self.salary_rule_id.tipo_entidad_asociada == 'afp':
                partner_id = self.slip_id.contract_id.afp_id.id
                encontro = True
            elif self.salary_rule_id.tipo_entidad_asociada == 'afc':
                partner_id = self.slip_id.contract_id.afc_id.id
                encontro = True
            elif self.salary_rule_id.tipo_entidad_asociada == 'eps':
                partner_id = self.slip_id.contract_id.eps_id.id
                encontro = True
            elif self.salary_rule_id.tipo_entidad_asociada == 'ccf':
                partner_id = self.slip_id.contract_id.ccf_id.id
                encontro = True

        if line.salary_rule_id.tercero and encontro is False:
            if line.salary_rule_id.campo_contrato == 'pension_id':
                partner_id = line.slip_id.contract_id.pension_id.id
            elif line.salary_rule_id.campo_contrato == 'eps_id':
                partner_id = line.slip_id.contract_id.eps_id.id
            elif line.salary_rule_id.campo_contrato == 'cesantias_id':
                partner_id = line.slip_id.contract_id.cesantias_id.id
            elif line.salary_rule_id.campo_contrato == 'arl_id':
                partner_id = line.slip_id.contract_id.arl_id.id
            elif line.salary_rule_id.campo_contrato == 'caja_id':
                partner_id = line.slip_id.contract_id.caja_id.id
            elif line.salary_rule_id.campo_contrato == 'otros_uno_id':
                partner_id = line.slip_id.contract_id.otros_uno_id.id
            elif line.salary_rule_id.campo_contrato == 'otros_dos_id':
                partner_id = line.slip_id.contract_id.otros_dos_id.id
            elif line.salary_rule_id.campo_contrato == 'otros_tres_id':
                partner_id = line.slip_id.contract_id.otros_tres_id.id
            elif line.salary_rule_id.campo_contrato == 'otros_cuatro_id':
                partner_id = line.slip_id.contract_id.otros_cuatro_id.id
            elif line.salary_rule_id.campo_contrato == 'otros_cinco_id':
                partner_id = line.slip_id.contract_id.otros_cinco_id.id
            elif line.salary_rule_id.campo_contrato == 'otros_seis_id':
                partner_id = line.slip_id.contract_id.otros_seis_id.id
            elif line.salary_rule_id.campo_contrato == 'otros_siete_id':
                partner_id = line.slip_id.contract_id.otros_siete_id.id
            elif line.salary_rule_id.campo_contrato == 'otros_ocho_id':
                partner_id = line.slip_id.contract_id.otros_ocho_id.id
            elif line.salary_rule_id.campo_contrato == 'otros_nueve_id':
                partner_id = line.slip_id.contract_id.otros_nueve_id.id
            elif line.salary_rule_id.campo_contrato == 'otros_diez_id':
                partner_id = line.slip_id.contract_id.otros_diez_id.id
            else:
                partner_id = line.partner_id.id
        elif line.salary_rule_id.empleado and encontro is False:
            partner_id = line.slip_id.employee_id.address_home_id.id
        else:
            if encontro is False:
                partner_id = line.partner_id.id

        if not partner_id:
            if not self.company_id.batch_payroll_move_lines and line.code == "NET":
                partner_id = self.employee_id.work_contact_id
            else:
                partner_id = line.partner_id.id
        return {
            'name': line.name,
            'partner_id': partner_id,   #partner.id,
            'account_id': account_id,
            'journal_id': line.slip_id.struct_id.journal_id.id,
            'date': date,
            'debit': debit,
            'credit': credit,
            'analytic_distribution': (line.salary_rule_id.analytic_account_id and {line.salary_rule_id.analytic_account_id.id: 100}) or
                                     (line.slip_id.contract_id.analytic_account_id.id and {line.slip_id.contract_id.analytic_account_id.id: 100})
        }
