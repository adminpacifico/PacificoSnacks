# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
           
class Hr_payroll_data(models.Model):
    _name = "hr.payroll_data"
    _description = "Precarga de data para iniciar nomina"
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    contract_id = fields.Many2one('hr.contract', string='Contrato')
    salario_base = fields.Float(default=0, string="Salario Base")
    dias = fields.Integer(default=0, string="Dias")
    sueldo = fields.Float(default=0, string="Sueldo")
    dias_no_laborados = fields.Integer(default=0, string="Dias no laborados")
    dias_inc = fields.Integer(default=0, string="Dias inc")
    incapacidad = fields.Integer(default=0, string="Incapacidad")
    dias_vacaciones = fields.Integer(default=0, string="Dias Vacaciones")
    valor_vacaciones = fields.Float(default=0, string="Valor Vacaciones")
    horas_extras_recargos_bonificacion = fields.Float(default=1, string="Horas Extras Recargos Bonificación")
    auxilio_transporte = fields.Float(default=0, string="Auxilio De Transporte")
    total_devengado = fields.Float(default=0, string="Total Devengado")
    salud = fields.Float(default=0, string="Salud")
    pension = fields.Float(default=0, string="Pension")
    fsp = fields.Float(default=0, string="FSP")
    retencion = fields.Float(default=0, string="Retención")
    descuentos = fields.Float(default=0, string="Descuentos")
    total_deduciones = fields.Float(default=0, string="Total Deduciones")
    total_pagar = fields.Float(default=0, string="Total a Pagar")
    fecha_inicial = fields.Date(string='Fecha inicial')
    fecha_final = fields.Date(string='Fecha final')

    @api.onchange('employee_id')
    def onchange_employee(self):
        for record in self:
            if record.employee_id:
                contract = self.env["hr.contract"].search([('employee_id', '=', record.employee_id.id),('state','=','open')], limit=1)
                if contract:
                    record.contract_id=contract.id
                else:
                    raise UserError(_('El empleado %s no tiene un contracto.') % (record.employee_id.name,))