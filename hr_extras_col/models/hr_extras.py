# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
           
class HrExtras(models.Model):
    _name = "hr.extras"
    _inherit = ['mail.thread']
    _description = "Hr Extras"
    _order = "name desc, id desc"


    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'), ('cancel','Cancelled')], 
                                    string='State', track_visibility='onchange', default='draft')
    name = fields.Char('Name', readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Empleado', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string='Contracto', track_visibility='onchange')
    date = fields.Date('Fecha', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    amount = fields.Float(string='Cantidad Horas', default=False ,readonly=True, states={'draft': [('readonly', False)]})
    hour_value = fields.Float(string="Valor Hora", compute='get_hour_value', store=True)
    total_money = fields.Float(string="Valor Total", compute='get_amount_money', store=True)
    load_manual = fields.Boolean(string="Cargue manual", default=False)
    total_money_manual = fields.Float(string="Valor Total (manual)", default=0.0,)
    payslip_id = fields.Many2one('hr.payslip', string='Payslip', readonly=True)
    input_id = fields.Many2one('hr.payslip.input.type', string='Tipo de hora extra', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})


    _sql_constraints = [
        ('employee_date_input_uniq', 'unique(date, input_id, employee_id)',
            'La novedad debe ser única por empleado!'),
    ]

    @api.constrains('amount')
    def _check_values(self):
        if self.amount == 0.0:
            raise Warning(_('La Cantidad de horas pueden ser cero. '))


    def name_get(self):
        return [(hour.id, '%s - %s' % (hour.employee_id.name, hour.date)) for hour in self]

    @api.depends('input_id', 'total_money_manual', 'contract_id' )
    def get_hour_value(self):
        for record in self:
            if record.total_money_manual == 0.0 and record.input_id != False:
                record.hour_value = (record.contract_id.wage / 240) * (record.input_id.hour_percentage)
            else:
                if not record.amount == 0.0:
                    record.hour_value =  record.total_money_manual/record.amount
                else:
                    record.hour_value = 0

    @api.depends('hour_value', 'total_money_manual', 'amount')
    def get_amount_money(self):
        for record in self:
            if record.total_money_manual == False or record.total_money_manual == 0.0 :
                record.total_money = record.hour_value * record.amount
            else:
                record.total_money = record.total_money_manual


    @api.onchange('employee_id','date')
    def onchange_employee(self):
        for hour in self:
            if hour.employee_id:
                contract = self.env["hr.contract"].search([('employee_id', '=', hour.employee_id.id),('state','=','open')], limit=1)
                if contract:
                    hour.contract_id=contract.id
                    hour.name = hour.employee_id.name + ' - ' + str(hour.date)
                else:
                    raise UserError(_('El empleado %s no tiene un contracto.') % (hour.employee_id.name,))
                    hour.name = hour.employee_id.name + ' - ' + str(hour.date)


    def action_approve_input(self):
        self.write({'state': 'approved'})



    def action_cancelled_approved_input(self):
        self.write({'state': 'cancel'})



    def action_draft_input(self):
        self.write({'state': 'draft'})



    def action_cancelled_input(self):
        if not self.payslip_id:
            self.write({'state': 'cancel'})