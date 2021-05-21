# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
           
class HrRuleInput(models.Model):
    _inherit = 'hr.rule.input'


    type_input = fields.Selection([ ('hours', 'Hours'),
                                    ('ingresos', 'Ingresos'),
                                    ('descuentos', 'Descuentos')], 'Input Type') 