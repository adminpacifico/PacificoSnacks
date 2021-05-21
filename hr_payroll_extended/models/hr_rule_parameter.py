# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

import odoo.addons.decimal_precision as dp

class HrRuleParameter(models.Model):
    _inherit = "hr.rule.parameter"


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
            'struct_id': 1,
        }
        salary_rule_id = self.env['hr.salary.rule'].create(values)
        if salary_rule_id:
            self.salary_rule_id = salary_rule_id.id
        return True