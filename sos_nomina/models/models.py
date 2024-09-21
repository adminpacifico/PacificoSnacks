from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class HrContract(models.Model):
    _inherit = 'hr.contract'

    auxilio_transporte = fields.Selection([
        ('no_tte','No Aplica'),
        ('en_dinero', 'En Dinero'),
        ('especie', 'En Especie'),
        ('menor_2', 'Menor a 2 SMLMV')
    ], string='Auxilio de Transporte', required=True, default='menor_2')
    
    schedule_pay = fields.Selection(selection_add=[('quincenal', 'Quincenal')])

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'    

    def compute_rule(self, localdict):
        contract_obj = self.env['hr.contract']
        payslip_obj = self.env['hr.payslip']
        return super(HrSalaryRule, self).compute_rule(localdict)
