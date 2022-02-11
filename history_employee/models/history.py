# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class DepartmentDetails(models.Model):
    _inherit = 'hr.employee'

    @api.onchange('department_id')
    def _onchange_department(self):
        employee_id = self.env['hr.employee'].search([('id', '=', self._origin.id)])
        vals = {
            'employee_id': self._origin.id,
            'employee_name': employee_id.name,
            'updated_date': datetime.now(),
            'changed_field': 'Department',
            'current_value': self.department_id.name

        }
        self.env['department.history'].sudo().create(vals)

    @api.onchange('job_id')
    def onchange_job_id(self):
        employee_id = self.env['hr.employee'].search([('id', '=', self._origin.id)])
        vals = {
            'employee_id': self._origin.id,
            'employee_name': employee_id.name,
            'updated_date': datetime.today(),
            'changed_field': 'Job Position',
            'current_value': self.job_id.name

        }
        self.env['department.history'].sudo().create(vals)

    @api.onchange('timesheet_cost')
    def _onchange_timesheet_cost(self):
        employee_id = self.env['hr.employee'].search([('id', '=', self._origin.id)])
        vals = {
            'employee_id': self._origin.id,
            'employee_name': employee_id.name,
            'updated_date': datetime.now(),
            'current_value': self.timesheet_cost
        }
        self.env['timesheet.cost'].sudo().create(vals)

    
    def department_details(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('hr.group_hr_manager'):
            return {
                'name': _("Department History"),
                'view_mode': 'tree',
                'res_model': 'department.history',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'domain': [('employee_id', '=', self.id)],
            }
        elif self.id == self.env.user.employee_id.id:
            return {
                'name': _("Department History"),
                'view_mode': 'tree',
                'res_model': 'department.history',
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
        else:
            raise UserError('You cannot access this field!!!!')

    
    def time_sheet(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('hr.group_hr_manager'):
            return {
                'name': _("Timesheet Cost Details"),
                'view_mode': 'tree',
                'res_model': 'timesheet.cost',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'domain': [('employee_id', '=', self.id)]
            }
        elif self.id == self.env.user.employee_id.id:
            return {
                'name': _("Timesheet Cost Details"),
                'view_mode': 'tree',
                'res_model': 'timesheet.cost',
                'type': 'ir.actions.act_window',
                'target': 'new'
            }
        else:
            raise UserError('You cannot access this field!!!!')

    
    def salary_history(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('hr.group_hr_manager'):
            return {
                'name': _("Historial de salario"),
                'view_mode': 'tree,form',
                'res_model': 'salary.history',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [('employee_id', '=', self.id)]
            }
        elif self.id == self.env.user.employee_id.id:
            return {
                'name': _("Historial de salario"),
                'view_mode': 'tree,form',
                'res_model': 'salary.history',
                'type': 'ir.actions.act_window',
                'target': 'current'
            }
        else:
            raise UserError('You cannot access this field!!!!')

    
    def contract_history(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('hr.group_hr_manager'):
            return {
                'name': _("Contract History"),
                'view_mode': 'tree,form',
                'res_model': 'contract.history',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [('employee_id', '=', self.id)]
            }
        if self.id == self.env.user.employee_id.id:
            return {
                'name': _("Contract History"),
                'view_mode': 'tree,form',
                'res_model': 'contract.history',
                'type': 'ir.actions.act_window',
                'target': 'current'
            }
        else:
            raise UserError('You cannot access this field!!!!')


class WageDetails(models.Model):
    _inherit = 'hr.contract'

    @api.onchange('wage')
    def onchange_wage(self):
        search_ids = self.env['hr.contract'].search([])[-1].id
        last_id = search_ids + 1
        vals = {
            'employee_id': self.employee_id.id,
            'contract': self._origin.id or last_id,
            'updated_date': datetime.today(),
            'current_value': self.wage,

        }
        self.env['salary.history'].sudo().create(vals)

    @api.onchange('name')
    def onchange_name(self):
        search_ids = self.env['hr.contract'].search([])[-1].id
        last_id = search_ids + 1
        vals = {
            'employee_id': self.employee_id.id,
            'contract': self._origin.id or last_id,
            'updated_date': datetime.today(),
            'changed_field': 'Referencia del contrato',
            'current_value': self.name,

        }
        self.env['contract.history'].create(vals)

    @api.onchange('date_start')
    def onchange_datestart(self):
        search_ids = self.env['hr.contract'].search([])[-1].id
        last_id = search_ids + 1
        vals = {
            'employee_id': self.employee_id.id,
            'contract': self._origin.id or last_id,
            'updated_date': datetime.today(),
            'changed_field': 'Fecha de inicio',
            'current_value': self.date_start,

        }
        self.env['contract.history'].create(vals)

    @api.onchange('date_end')
    def onchange_dateend(self):
        search_ids = self.env['hr.contract'].search([])[-1].id
        last_id = search_ids + 1
        vals = {
            'employee_id': self.employee_id.id,
            'contract': self._origin.id or last_id,
            'updated_date': datetime.today(),
            'changed_field': 'Fecha final',
            'current_value': self.date_end,

        }
        self.env['contract.history'].create(vals)


class DepartmentHistory(models.Model):
    _name = 'department.history'

    employee_id = fields.Char(string='Employee Id', help="Employee")
    employee_name = fields.Char(string='Employee Name', help="Name")
    changed_field = fields.Char(string='Job position', help="Displays the changed department/job position")
    updated_date = fields.Date(string='Date', help="Display the date on which  department or job position changed")
    current_value = fields.Char(string='Designation', help="Display the designation")


class TimesheetCost(models.Model):
    _name = 'timesheet.cost'

    employee_id = fields.Char(string='Employee Id', help="Employee")
    employee_name = fields.Char(string='Employee Name', help="Name")
    updated_date = fields.Date(string='Updated On', help="Updated Date of Time Sheet")
    current_value = fields.Char(string='Current Cost', help="Updated Value of Time Sheet")


class SalaryHistory(models.Model):
    _name = 'salary.history'

    employee_id = fields.Many2one('hr.employee', string='Empleado')
    contract = fields.Char(string='Contrato ID')
    contract_id = fields.Many2one('hr.contract', string='Contracto', compute='get_contract_id')
    updated_date = fields.Date(string='Actualizado en', help="Fecha de actualización del salario")
    current_value = fields.Float(string='Salario actual', help="Salario actualizado")

    def get_contract_id(self):
        for record in self:
            if record.contract:
                contract = self.env["hr.contract"].search([('id', '=', int(record.contract))], limit=1)
                if contract:
                    record.contract_id = contract
                else:
                    record.contract_id = False
            else:
                record.contract_id = False

    @api.onchange('employee_id')
    def onchange_employee(self):
        for record in self:
            if record.employee_id:
                contract = self.env["hr.contract"].search([('employee_id', '=', record.employee_id.id), ('state', '=', 'open')], limit=1)
                if contract:
                    record.contract = str(contract.id)
                else:
                    raise UserError(_('El empleado %s no tiene un contracto.') % (record.employee_id.name,))


class ContractHistory(models.Model):
    _name = 'contract.history'

    employee_id = fields.Many2one('hr.employee', string='Empleado')
    contract = fields.Char(string='Contrato ID')
    contract_id = fields.Many2one('hr.contract', string='Contracto', compute='get_contract_id')
    updated_date = fields.Date(string='Actualizado en', help="Fecha de actualización de contrato")
    changed_field = fields.Char(string='Campo cambiado', help="Campo cambiado")
    current_value = fields.Char(string='Valor actualizado del contrato', help="Valor actualizado del contrato")

    def get_contract_id(self):
        for record in self:
            if record.contract:
                contract = self.env["hr.contract"].search([('id', '=', int(record.contract))], limit=1)
                if contract:
                    record.contract_id = contract
                else:
                    record.contract_id = False
            else:
                record.contract_id = False

