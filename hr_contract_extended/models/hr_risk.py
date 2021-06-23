# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
           
class HrRisk(models.Model):
    _name = "hr.risk"
    _inherit = ['mail.thread']
    _description = "Risk"
    _order = "name desc, id desc"   
    
    name = fields.Char('Nombre', required=True)
    code = fields.Char('Codigo', required=True)
    amount = fields.Float(string='Monto', required=True)
     

    def name_get(self):
        return [(risk.id, '%s - %s' % (risk.amount, risk.name)) for risk in self]