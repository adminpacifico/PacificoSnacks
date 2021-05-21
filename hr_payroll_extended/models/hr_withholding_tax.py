# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
           
class Hr_withholding_tax(models.Model):
    _name = "hr.withholding.tax"
    _inherit = ['mail.thread']
    _description = "Hr Retencion en la fuente"
    _order = "name desc, id desc"


    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'), ('cancel','Cancelled')], 
                                    string='State', track_visibility='onchange', default='draft')
    name = fields.Char('Name', readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Empleado', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string='Contrato', track_visibility='onchange')
    input_id = fields.Many2one('hr.payslip.input.type', string='Input', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    deductions_rt_id = fields.One2many('hr_deductions_rt', 'deductions_id', string='Deducciones')
    #loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)


    _sql_constraints = [
        ('employee_input_uniq', 'unique(input_id, employee_id)',
            'La entrada debe ser única por empleado!'),
    ]

    def name_get(self):
        return [(hour.id, '%s - %s' % (hour.employee_id.name, 'DEDUCCIONES')) for hour in self]

    @api.onchange('employee_id')
    def onchange_employee(self):
        for hour in self:
            if hour.employee_id:
                contract = self.env["hr.contract"].search([('employee_id', '=', hour.employee_id.id),('state','=','open')], limit=1)
                if contract:
                    hour.contract_id=contract.id
                    hour.name = hour.employee_id.name + ' - DEDUCCIONES'
                else:
                    raise UserError(_('El empleado %s no tiene un contracto.') % (hour.employee_id.name,))
                    hour.name = hour.employee_id.name + ' - DEDUCCIONES'


    def action_approve_input(self):
        self.write({'state': 'approved'})



    def action_cancelled_approved_input(self):
        self.write({'state': 'cancel'})



    def action_draft_input(self):
        self.write({'state': 'draft'})



    def action_cancelled_input(self):
        if not self.payslip_id:
            self.write({'state': 'cancel'})