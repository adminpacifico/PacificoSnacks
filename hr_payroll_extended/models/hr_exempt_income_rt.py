from odoo import fields, models, api
from odoo.exceptions import ValidationError

class hr_exempt_income_rt (models.Model):
    _name = 'hr_exempt_income_rt'
    _description = 'Renta exenta de retención en la fuente metodo 1'
    _rec_name = 'concept'

    date = fields.Date(string="Fecha", required='True', default=fields.Date.today())
    concept = fields.Many2one('hr_exempt_income_concepts', string='Concepto')
    amount = fields.Integer(default=1, string="Monto")
    exempt_income_id = fields.Many2one('hr_exempt_income_tax', string="Renta Exenta")
    #loan_id = fields.Many2one('hr.loan', string="Loan Ref.", help="Loan")








