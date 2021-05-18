from odoo import fields, models, api
from odoo.exceptions import ValidationError

class hr_deduction_concepts (models.Model):
    _name = 'hr_deduction_concepts'
    _description = 'Conceptos de Deducciones'
    _rec_name = 'name'

    name = fields.Char('nombre')

    _sql_constraints = [
        ('concept_id_uniq', 'unique(name)', "Ya existe este concepto!"),
    ]









