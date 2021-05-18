# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

import odoo.addons.decimal_precision as dp

class HrParameterPayslip(models.Model):
    _name = "hr.parameter.payslip"
    _description = "Parameter Paylsip"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name desc, id desc"    


    name = fields.Char('Name', required=True, tracking=True)
    code = fields.Char('Code', tracking=True)
    amount = fields.Float(default=0.0000, digits=dp.get_precision('Factor Rule'), tracking=True)
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Regla salarial', tracking=True)


    def generate_salary_rule(self):
        if self.salary_rule_id:
            self._cr.execute(''' UPDATE hr_salary_rule SET amount_fix=%s WHERE id=%s ''', (self.amount, self.salary_rule_id.id))
            return True
        category_id = self.env['hr.salary.rule.category'].search([('code', '=', 'INFO')])
        if not category_id:
            raise ValidationError(_("Debe existir una categoria con el codigo INFO"))        
        values = {
            'name': self.name,
            'code': self.code,
            'category_id': category_id.id,
            'amount_select': 'fix',
            'amount_fix': self.amount,
            'sequence': 1,
            'appears_on_payslip': False,
        }
        salary_rule_id = self.env['hr.salary.rule'].create(values)
        if salary_rule_id:
            self.salary_rule_id = salary_rule_id.id
        return True