# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date
from datetime import datetime


class GenerateHRWorkEntry(models.TransientModel):
    _name = "generate.hr.work.entry"

    date_start = fields.Date(
        string='Fecha de inicio', required=True
    )
    date_stop = fields.Date(
        string='Fecha final', required=True
    )
    company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True,
                                 default=lambda self: self.env.company)

    employee_id = fields.Many2one('hr.employee', string='Empleado')

    payslip_run_id = fields.Many2one('hr.payslip.run', string='Nomina')

    modo = fields.Selection(string="Modo", selection=[('1', 'Por Empleado'), ('2', 'Por Nomina')], default='1', required=True)

    def generate_work_entry(self):
        time_start = datetime.min.time()
        date_start = datetime.combine(self.date_start, time_start)
        time_stop = datetime.max.time()
        date_stop = datetime.combine(self.date_stop, time_stop)
        if self.modo == '1':
            vals_list = []
            contract_id = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
            vals_list += contract_id._get_work_entries_total_values(date_start, date_stop)
            self.env['hr.work.entry'].create(vals_list)

        elif self.modo == '2':
            payslip = self.env['hr.payslip'].search([('payslip_run_id', '=', self.payslip_run_id.id)])
            for record in payslip:
                vals_list = []
                contract_id = self.env['hr.contract'].search([('employee_id', '=', record.employee_id.id)])
                vals_list += contract_id._get_work_entries_total_values(date_start, date_stop)
                self.env['hr.work.entry'].create(vals_list)

        return {'type': 'ir.actions.act_window_close'}