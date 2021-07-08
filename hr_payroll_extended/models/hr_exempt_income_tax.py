# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class hr_exempt_income_tax (models.Model):
    _name = 'hr_exempt_income_tax'
    _inherit = ['mail.thread']
    _description = 'Renta exenta de retención en la fuente metodo 1'
    _order = "name desc, id desc"

    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'), ('cancel', 'Cancelled')],
                             string='State', track_visibility='onchange', default='draft')
    name = fields.Char('Name', readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Empleado', track_visibility='onchange', readonly=True,
                                  states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string='Contrato', track_visibility='onchange')
    input_id = fields.Many2one('hr.payslip.input.type', string='Input', track_visibility='onchange', readonly=True,
                               states={'draft': [('readonly', False)]})
    exempt_income_id = fields.One2many('hr_exempt_income_rt', 'exempt_income_id', string='Renta Exenta')
    # loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)

    _sql_constraints = [
        ('employee_input_uniq', 'unique(input_id, employee_id)',
         'La entrada debe ser única por empleado!'),
    ]

    def name_get(self):
        return [(hour.id, '%s - %s' % (hour.employee_id.name, 'RENTA EXENTA')) for hour in self]

    @api.onchange('employee_id')
    def onchange_employee(self):
        for hour in self:
            if hour.employee_id:
                contract = self.env["hr.contract"].search(
                    [('employee_id', '=', hour.employee_id.id), ('state', '=', 'open')], limit=1)
                if contract:
                    hour.contract_id = contract.id
                    hour.name = hour.employee_id.name + ' - RENTA EXENTA'
                else:
                    raise UserError(_('El empleado %s no tiene un contracto.'))
                    hour.name = hour.employee_id.name + ' - RENTA EXENTA'

    def action_approve_input(self):
        self.write({'state': 'approved'})

    def action_cancelled_approved_input(self):
        self.write({'state': 'cancel'})

    def action_draft_input(self):
        self.write({'state': 'draft'})

    def action_cancelled_input(self):
        if not self.payslip_id:
            self.write({'state': 'cancel'})








