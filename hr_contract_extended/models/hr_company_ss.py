# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
           
class HrCompanySS(models.Model):
    _name = "hr.company.ss"
    _description = "Company SS"
    _order = "id desc"   
    
    
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='restrict')
    entity = fields.Selection([('fc', 'Fondo de Cesantias'),
                               ('afp', 'AFP'),
                               ('arl', 'ARL'),
                               ('eps', 'EPS'),
                               ('fsp', 'FSP'),
                               ('icbf', 'ICBF'),
                               ('sena', 'Sena'),
                               ('ccf', 'Caja de Compensacion'),], string='Entidad', copy=False)
    contract_id = fields.Many2one('hr.contract', string='Contract')