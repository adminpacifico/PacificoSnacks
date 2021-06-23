# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
           
class HrCausalTermination(models.Model):
    _name = "hr.causal.termination"
    _inherit = ['mail.thread']
    _description = "Casual de terminacion de contrato"
    _order = "name desc, id desc"
    
    code = fields.Char('Codigo', required=True)
    name = fields.Char('Nombre', required=True)