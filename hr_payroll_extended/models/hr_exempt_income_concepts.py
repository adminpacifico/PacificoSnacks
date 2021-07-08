from odoo import fields, models, api
from odoo.exceptions import ValidationError

class hr_exempt_income_concepts (models.Model):
    _name = 'hr_exempt_income_concepts'
    _description = 'Conceptos de Renta Exenta'
    _rec_name = 'name'

    name = fields.Char('nombre')

    _sql_constraints = [
        ('concept_id_uniq', 'unique(name)', "Ya existe este concepto!"),
    ]









