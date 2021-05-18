from odoo import fields, models, api
from odoo.exceptions import ValidationError

class hr_deductions_rt (models.Model):
    _name = 'hr_deductions_rt'
    _description = 'Deducciones de retención en la fuente metodo 1'
    _rec_name = 'concept'

    date = fields.Date(string="Fecha", required='True', default=fields.Date.today())
    concept = fields.Many2one('hr_deduction_concepts', string='Concepto')
    amount = fields.Integer(default=1, string="Monto")
    deductions_id = fields.Many2one('hr.withholding.tax', string="Deduciones")
    #loan_id = fields.Many2one('hr.loan', string="Loan Ref.", help="Loan")








