# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
           
class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    code_input = fields.Char(string="Codigo de entrada")
    name_input = fields.Char(string="Descripción")