# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
           
class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    tag_id = fields.Many2one('account.analytic.tag', string="Etiqueta Analítica")