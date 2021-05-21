# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class HrTypePayslip(models.Model):
    _name = "hr.type.payslip"
    _description = "Type Paylsip"
    _order = "name desc, id desc"    


    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
    type = fields.Selection([
                    ('payslip', 'Payslip'),
                    ('liqui', 'Liquidation'),
                    ('other', 'Other')], 'Type')                      