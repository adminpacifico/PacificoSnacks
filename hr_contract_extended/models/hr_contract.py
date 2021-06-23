# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class HrContract(models.Model):
    _inherit = 'hr.contract'


    causal_termination_id = fields.Many2one('hr.causal.termination', string='Casual de terminacion de contrato')
    risk_id = fields.Many2one('hr.risk', string='Riesgos Laborales')
    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Activo'),
        ('close', 'Liquidado'),
        ('cancel', 'Liquidado'),
    ], string='Status', group_expand='_expand_states', copy=False,
       tracking=True, help='Status of the contract', default='draft')
    entity_ids = fields.One2many('hr.company.ss', 'contract_id', string='Entidad')

    @api.onchange('state')
    def _date_end_casual(self):
        for record in self:
            if record.state == 'cancel' and not record.date_end:
               record.date_end = date.today()