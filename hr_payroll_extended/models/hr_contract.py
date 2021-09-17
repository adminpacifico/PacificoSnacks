# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

from datetime import date, datetime, time
from collections import defaultdict
from odoo import api, fields, models
from odoo.tools import date_utils

from datetime import datetime
from datetime import date

import pytz

import logging

_logger = logging.getLogger(__name__)

def days360(s, e):
    return ( ((e.year * 12 + e.month) * 30 + e.day) - ((s.year * 12 + s.month) * 30 + s.day))
           
class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """
    _inherit = "hr.contract"
    _description = "Employee Contract"

    # Informacion salarial
    retention_method = fields.Selection(string='Metodo de rétencion', selection=[('NA', 'No aplica'),('M1', 'Metodo 1'),('M2', 'Metodo 2')], default='NA', required=True )
    integral_salary = fields.Boolean(string="Salario Integral", default=False)

    # Historial de vacciones
    vacation_initial = fields.Float(string="Vacaciones iniciales Disfrutadas", default=0)
    accumulated_vacation = fields.Float(string="Vacaciones Acumuladas", compute='get_accumulated_vacation' )
    vacation_used = fields.Float(string="Vacaciones Disfrutadas", compute='get_vacation_used')
    vacations_available = fields.Float(string="Vacaciones Disponibles", compute='get_vacations_available')
    vacations_history = fields.Many2many('hr.leave' ,string="Historial", compute='get_history')
    vacations_date = fields.Date(string="Periodo Trabajado promedio", compute='get_vacations_date')

    # Suspencion de trabajo
    suspension = fields.Float(string="Suspensión de trabajo", compute='get_suspension')
    suspension_history = fields.Many2many('hr.leave', string="Historial", compute='get_suspension_history')

    # Auxilios
    aux_movilizacion = fields.Boolean(string="Auxilio Movilización", default=False)
    aux_movilizacion_amount = fields.Float(string="Monto Mensual")
    aux_rodamiento = fields.Boolean(string="Auxilio Rodamiento", default=False)
    aux_rodamiento_amount = fields.Float(string="Monto Mensual")


    @api.onchange('wage')
    def _integral_salary(self):
        wage_min = self.env['hr.salary.rule'].search([("code", "=", 'SMLMV')], limit=1).amount_fix
        if wage_min:
            for record in self:
                if record.wage >= (wage_min*10):
                    record.integral_salary = True
                else:
                    record.integral_salary = False

    def get_vacations_date(self):
        for record in self:
            dias_promedio_trabajado = (record.vacation_used * 365) / 15
            record.vacations_date = record.date_start + relativedelta(days=int(dias_promedio_trabajado))

    def get_accumulated_vacation(self):
        for record in self:
            date_from = datetime.combine(record.date_start, datetime.min.time())
            if record.date_end != False and record.date_end <= date.today():
                date_to = datetime.combine(record.date_end, datetime.max.time())
            else:
                date_to = datetime.combine(date.today(), datetime.max.time())
           # time_worked = self.env['hr.leave']._get_number_of_days(date_from, date_to, self.employee_id.id)['days']
           # time_worked = (date_to - date_from).days
            time_worked = days360( date_from ,date_to)
            time_worked = time_worked+1
            if float(time_worked) > 0:
                accumulated_vacation = (time_worked/30) * 1.25
            else:
                accumulated_vacation = 0
            record.accumulated_vacation = accumulated_vacation

    def get_vacation_used(self):
        for record in self:
            vacations = record.env['hr.leave'].search([('employee_id', '=', record.employee_id.id), ('contract_id', '=', record.id), ('holiday_status_id.code', 'in', ('VACATIONS','VACATIONS_MONEY','VACATIONS_LIQ','VACATIONS_MONEY_LIQ')), ('state', '=', 'validate')])
            vacation_used = 0
            for vacation in vacations:
                vacation_used = vacation_used + vacation.workday

            record.vacation_used = vacation_used + record.vacation_initial

    def get_vacations_available(self):
        for record in self:
            record.vacations_available = record.accumulated_vacation - record.vacation_used

    def get_history(self):
        for record in self:
            record.vacations_history = record.env['hr.leave'].search([('employee_id', '=', record.employee_id.id), ('contract_id', '=', record.id), ('holiday_status_id.code', 'in', ('VACATIONS','VACATIONS_MONEY','VACATIONS_LIQ','VACATIONS_MONEY_LIQ')), ('state', '=', 'validate')])

    def get_suspension(self):
        for record in self:
            suspensions = record.env['hr.leave'].search([('employee_id', '=', record.employee_id.id), ('contract_id', '=', record.id), ('holiday_status_id.code','=','SUSPENSION'), ('state', '=', 'validate')])
            suspension = 0
            for s in suspensions:
                suspension = suspension + s.workday
            record.suspension = suspension

    def get_suspension_history(self):
        for record in self:
            record.suspension_history = record.env['hr.leave'].search([('employee_id', '=', record.employee_id.id), ('contract_id', '=', record.id), ('holiday_status_id.code','=','SUSPENSION'), ('state', '=', 'validate')])

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by
                 hierachy (parent=False first, then first level children and
                 so on) and without duplicata
        """
        structures = self.mapped("struct_id")
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))

    def _get_exceed_hours(self, date_from, date_to):

        generated_date_max = min(fields.Date.to_date(date_to), date_utils.end_of(fields.Date.today(), 'month'))
        self._generate_work_entries(date_from, generated_date_max)
        date_from = datetime.combine(date_from, datetime.min.time())
        date_to = datetime.combine(date_to, datetime.max.time())
        exceed_work_data = defaultdict(int)

        work_entries = self.env['hr.work.entry'].search(
            [
                '&', '&',
                ('state', 'in', ['validated', 'draft']),
                ('contract_id', 'in', self.ids),
                '|', '|', '&', '&',
                ('date_start', '>=', date_from),
                ('date_start', '<', date_to),
                ('date_stop', '>', date_to),
                '&', '&',
                ('date_start', '<', date_from),
                ('date_stop', '<=', date_to),
                ('date_stop', '>', date_from),
                '&',
                ('date_start', '<', date_from),
                ('date_stop', '>', date_to),
            ]
        )

        for work_entry in work_entries:
            date_start = work_entry.date_start
            date_stop = work_entry.date_stop
            if work_entry.work_entry_type_id.is_leave:
                contract = work_entry.contract_id
                calendar = contract.resource_calendar_id
                employee = contract.employee_id
                contract_data = employee._get_work_days_data_batch(
                    date_start, date_stop, compute_leaves=False, calendar=calendar
                )[employee.id]

                exceed_work_data[work_entry.work_entry_type_id.id] += contract_data.get('hours', 0)
            else:
                dt = date_stop - date_start
                exceed_work_data[work_entry.work_entry_type_id.id] += dt.days * 24 + dt.seconds / 3600  # Number of hours
        return exceed_work_data

    def _get_work_entries_total_values(self, date_start, date_stop):
        """
        Generate a work_entries list between date_start and date_stop for one contract.
        :return: list of dictionnary.
        """
        default_work_entry_type = self.structure_type_id.default_work_entry_type_id
        vals_list = []

        for contract in self:
            contract_vals = []
            employee = contract.employee_id
            calendar = contract.resource_calendar_id
            #calendar = self.env['resource.calendar'].search([("name", "=", 'NOMINA')], limit=1)
            resource = employee.resource_id
            tz = pytz.timezone(calendar.tz)
            #if not calendar:
            #    calendar = contract.resource_calendar_id

            attendances = calendar._work_intervals_batch(
                pytz.utc.localize(date_start) if not date_start.tzinfo else date_start,
                pytz.utc.localize(date_stop) if not date_stop.tzinfo else date_stop,
                resources=resource, tz=tz
            )[resource.id]
            # Attendances
            for interval in attendances:
                work_entry_type_id = interval[2].mapped('work_entry_type_id')[:1] or default_work_entry_type
                # All benefits generated here are using datetimes converted from the employee's timezone
                contract_vals += [{
                    'name': "%s: %s" % (work_entry_type_id.name, employee.name),
                    'date_start': interval[0].astimezone(pytz.utc).replace(tzinfo=None),
                    'date_stop': interval[1].astimezone(pytz.utc).replace(tzinfo=None),
                    'work_entry_type_id': work_entry_type_id.id,
                    'employee_id': employee.id,
                    'contract_id': contract.id,
                    'company_id': contract.company_id.id,
                    'state': 'draft',
                }]

            # Leaves
            leaves = self.env['resource.calendar.leaves'].sudo().search([
                ('resource_id', 'in', [False, resource.id]),
                ('calendar_id', '=', calendar.id),
                ('date_from', '<', date_stop),
                ('date_to', '>', date_start)
            ])

            for leave in leaves:
                start = max(leave.date_from, datetime.combine(contract.date_start, datetime.min.time()))
                end = min(leave.date_to, datetime.combine(contract.date_end or date.max, datetime.max.time()))
                if leave.holiday_id:
                    work_entry_type = leave.holiday_id.holiday_status_id.work_entry_type_id
                else:
                    work_entry_type = leave.mapped('work_entry_type_id')
                contract_vals += [{
                    'name': "%s%s" % (work_entry_type.name + ": " if work_entry_type else "", employee.name),
                    'date_start': start,
                    'date_stop': end,
                    'work_entry_type_id': work_entry_type.id,
                    'employee_id': employee.id,
                    'leave_id': leave.holiday_id and leave.holiday_id.id,
                    'company_id': contract.company_id.id,
                    'state': 'draft',
                    'contract_id': contract.id,
                }]

            # If we generate work_entries which exceeds date_start or date_stop, we change boundaries on contract
            if contract_vals:
                date_stop_max = max([x['date_stop'] for x in contract_vals])
                if date_stop_max > contract.date_generated_to:
                    contract.date_generated_to = date_stop_max

                date_start_min = min([x['date_start'] for x in contract_vals])
                if date_start_min < contract.date_generated_from:
                    contract.date_generated_from = date_start_min

            vals_list += contract_vals

        return vals_list
