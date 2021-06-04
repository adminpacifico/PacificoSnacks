# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
           
class HrRuleInput(models.Model):
    _inherit = 'hr.payslip.input.type'


    type_input = fields.Selection([ ('hours', 'Horas Extras'),
                                    ('ingresos', 'Ingresos'),
                                    ('descuentos', 'Descuentos'),
                                    ('tasa_incapacidad', 'Tasa Incapacidad'),
                                    ('otros', 'Otros')], 'Tipo de Entrada')

    hour_percentage = fields.Float(string='Porcentaje Hora', default=0.0)
    disability_percentage = fields.Float(string='Porcentaje Incapacidad', default=0.0)