<<<<<<< HEAD
# -*- coding: utf-8 -*-
import logging
import math

from collections import namedtuple

from datetime import datetime, date, timedelta, time
from pytz import timezone, UTC

from odoo import api, fields, models, SUPERUSER_ID, tools
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools.translate import _
from odoo.osv import expression
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError
import pytz
_logger = logging.getLogger(__name__)
import dateutil.parser
from dateutil.relativedelta import relativedelta

# Used to agglomerate the attendances in order to find the hour_from and hour_to
# See _onchange_request_parameters
DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')

def days_between(start_date, end_date):
    #Add 1 day to end date to solve different last days of month
    #s1, e1 =  datetime.strptime(start_date,"%Y-%m-%d") , datetime.strptime(end_date,"%Y-%m-%d")  + timedelta(days=1)
    s1, e1 =  start_date , end_date + timedelta(days=1)
    #Convert to 360 days
    s360 = (s1.year * 12 + s1.month) * 30 + s1.day
    e360 = (e1.year * 12 + e1.month) * 30 + e1.day
    #Count days between the two 360 dates and return tuple (months, days)
    res = divmod(e360 - s360, 30)
    return ((res[0] * 30) + res[1]) or 0

class HrLeave(models.Model):
    _inherit = 'hr.leave'


    days_paid = fields.Float(
        string='Dias Pagados', 
        default='0.0'
        
    )

    days_vacations = fields.Integer(string="Vacaciones Disponibles", compute='get_days_vacations')
    amount_vacations = fields.Float(string="Valor Pagado", compute='get_amount_vacations')
    total_number_of_days = fields.Float(string="Duración Total", compute='get_total_number_of_days')
    amount_vacations_old = fields.Float(string="Valor Pagado (Carga Manual)", default=0,)

    @api.depends('employee_id')
    def get_days_vacations(self):
        for record in self:
            contracts = record.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
            if contracts:
                for contract in contracts:
                    record.days_vacations = contract.vacations_available
            else:
                record.days_vacations = 0

    def get_total_number_of_days(self):
        for record in self:
            if record.request_date_to and record.request_date_from:
                record.total_number_of_days = (record.request_date_to - record.request_date_from).days + 1
            else:
                record.total_number_of_days = 0

    def get_amount_vacations(self):
        for record in self:
            if record.amount_vacations_old == 0:
                contracts = record.env['hr.contract'].search([('employee_id', '=', record.employee_id.id)])
                if contracts and record.holiday_status_id.id == 6 :
                    for contract in contracts:
                        salary = contract.wage
                        total_extra_hour = 0
                        total_bonus = 0
                        date_from = str(record.date_from)
                        date_from = dateutil.parser.parse(date_from).date()
                        date_to = str(record.date_to)
                        date_to = dateutil.parser.parse(date_to).date()
                        horas_extras_12month_before = record.env['hr.payslip'].get_inputs_hora_extra_12month_before(contract, date_from, date_to)
                        if horas_extras_12month_before:
                            hm12_date_ini = date_to - relativedelta(months=12)
                            if contract.date_start <= hm12_date_ini:
                                hm12_date_init = hm12_date_ini
                            else:
                                hm12_date_init = contract.date_start
                            total_days12y = days_between(hm12_date_init, date_to)
                            amounth25 = 0
                            amounth35 = 0
                            amounth75 = 0
                            amounthf75 = 0
                            amounth110 = 0
                            for hora in horas_extras_12month_before:
                                if hora[1] == 'RECARGONOCTURNO':
                                    amounth35 = amounth35 + hora[2]
                                if hora[1] == 'RECARGODIURNOFESTIVO':
                                    amounthf75 = amounthf75 + hora[2]
                                if hora[1] == 'RECARGONOCTURNOFESTIVO':
                                    amounth110 = amounth110 + hora[2]
                                if hora[1] == 'EXTRADIURNA':
                                    amounth25 = amounth25 + hora[2]
                                if hora[1] == 'EXTRANOCTURNA':
                                    amounth75 = amounth75 + hora[2]

                            if not amounth25 == 0:
                                amounth25 = round(((amounth25 / total_days12y) * 30), 2)
                                percentage = record.env['hr.salary.rule'].search([("code", "=", 'P_EXTRADIURNA')],
                                                                               limit=1).amount_fix
                                if percentage:
                                    amounth_hour = round(((salary / 240) * percentage), 2)
                                    amounth25 = round((amounth25 * amounth_hour), 2)
                                else:
                                    amounth_hour = round((salary / 240), 2)
                                    amounth25 = round((amounth25 * amounth_hour), 2)
                            if not amounth35 == 0:
                                amounth35 = round(((amounth35 / total_days12y) * 30), 2)
                                percentage = record.env['hr.salary.rule'].search([("code", "=", 'P_RECARGONOCTURNO')],limit=1).amount_fix
                                if percentage:
                                    amounth_hour = round(((salary / 240) * percentage), 2)
                                    amounth35 = round((amounth35 * amounth_hour), 2)
                                else:
                                    amounth_hour = round((salary / 240), 2)
                                    amounth35 = round((amounth35 * amounth_hour), 2)
                            if not amounth75 == 0:
                                amounth75 = round(((amounth75 / total_days12y) * 30), 2)
                                percentage = record.env['hr.salary.rule'].search([("code", "=", 'P_EXTRANOCTURNA')],
                                                                               limit=1).amount_fix
                                if percentage:
                                    amounth_hour = round(((salary / 240) * percentage), 2)
                                    amounth75 = round((amounth75 * amounth_hour), 2)
                                else:
                                    amounth_hour = round((salary / 240), 2)
                                    amounth75 = round((amounth75 * amounth_hour), 2)
                            if not amounthf75 == 0:
                                amounthf75 = round(((amounthf75 / total_days12y) * 30), 2)
                                percentage = record.env['hr.salary.rule'].search([("code", "=", 'P_RECARGODIURNOFESTIVO')],
                                                                               limit=1).amount_fix
                                if percentage:
                                    amounth_hour = round(((salary / 240) * percentage), 2)
                                    amounthf75 = round((amounthf75 * amounth_hour), 2)
                                else:
                                    amounth_hour = round((salary / 240), 2)
                                    amounthf75 = round((amounthf75 * amounth_hour), 2)
                            if not amounth110 == 0:
                                amounth110 = round(((amounth110 / total_days12y) * 30), 2)
                                percentage = record.env['hr.salary.rule'].search([("code", "=", 'P_RECARGONOCTURNOFESTIVO')],
                                                                               limit=1).amount_fix
                                if percentage:
                                    amounth_hour = round(((salary / 240) * percentage), 2)
                                    amounth110 = round((amounth110 * amounth_hour), 2)
                                else:
                                    amounth_hour = round((salary / 240), 2)
                                    amounth110 = round((amounth110 * amounth_hour), 2)

                            total_extra_hour = amounth25 + amounth35 + amounth75 + amounthf75 + amounth110
                        inputs_loans_12month_before = record.env['hr.payslip'].get_inputs_loans_12month_before(contract, date_from, date_to)
                        if inputs_loans_12month_before:
                            lm12_date_ini = date_to - relativedelta(months=12)
                            if contract.date_start <= lm12_date_ini:
                                lm12_date_init = lm12_date_ini
                            else:
                                lm12_date_init = contract.date_start
                            total_dayl12 = days_between(lm12_date_init, date_to)
                            total_bonus = 0
                            for loans in inputs_loans_12month_before:
                                if loans[1] == 'BONIFICACION':
                                    total_bonus = total_bonus + loans[2]
                            if not total_bonus == 0:
                                total_bonus = round((total_bonus/total_dayl12)*30, 2)
                        record.amount_vacations = round((((salary + total_bonus + total_extra_hour)/30) * record.number_of_days),2)
                else:
                    record.amount_vacations = 0
            else:
                record.amount_vacations = record.amount_vacations_old

    '''
    def write(self, values):
        # El 6 corresponde al tipo de ausencia de vacaciones, en caso de modificar el registro se debe cambiar el numero a evaluar
        if self.holiday_status_id.id == 6 and self.days_vacations < self.number_of_days:
            raise Warning('¡No es posible registrar la ausencia! '
                          'El empleado no tiene suficientes días de vacaciones ('+str(self.days_vacations)+')')
        return super(HrLeave, self).write(values)
    '''

    def _create_resource_leave(self):
        """ This method will create entry in resource calendar time off object at the time of holidays validated
        :returns: created `resource.calendar.leaves`
        """
        vals_list = []
        calendar = self.employee_id.resource_calendar_id
        resource = self.employee_id.resource_id
        tz = pytz.timezone(calendar.tz)
        attendances = calendar._work_intervals_batch(
            pytz.utc.localize(self.date_from) if not self.date_from.tzinfo else self.date_from,
            pytz.utc.localize(self.date_to) if not self.date_to.tzinfo else self.date_to,
            resources=resource, tz=tz
        )[resource.id]
        # Attendances
        for interval in attendances:
            # All benefits generated here are using datetimes converted from the employee's timezone
            vals_list += [{
                'name': self.name,
                'date_from': interval[0].astimezone(pytz.utc).replace(tzinfo=None),
                'holiday_id': self.id,
                'date_to': interval[1].astimezone(pytz.utc).replace(tzinfo=None),
                'resource_id': self.employee_id.resource_id.id,
                'calendar_id': self.employee_id.resource_calendar_id.id,
                'time_type': self.holiday_status_id.time_type,
            }]
        return self.env['resource.calendar.leaves'].sudo().create(vals_list)



    # @api.onchange('request_date_from_period', 'request_hour_from', 'request_hour_to',
    #               'request_date_from', 'request_date_to',
    #               'employee_id')
    # def _onchange_request_parameters(self):
    #     if not self.request_date_from:
    #         self.date_from = False
    #         return

    #     if self.request_unit_half or self.request_unit_hours:
    #         self.request_date_to = self.request_date_from

    #     if not self.request_date_to:
    #         self.date_to = False
    #         return

    #     resource_calendar_id = self.employee_id.resource_calendar_id or self.env.company.resource_calendar_id
    #     domain = [('calendar_id', '=', resource_calendar_id.id), ('display_type', '=', False)]
    #     attendances = self.env['resource.calendar.attendance'].read_group(domain, ['ids:array_agg(id)', 'hour_from:min(hour_from)', 'hour_to:max(hour_to)', 'week_type', 'dayofweek', 'day_period'], ['week_type', 'dayofweek', 'day_period'], lazy=False)

    #     # Must be sorted by dayofweek ASC and day_period DESC
    #     attendances = sorted([DummyAttendance(group['hour_from'], group['hour_to'], group['dayofweek'], group['day_period'], group['week_type']) for group in attendances], key=lambda att: (att.dayofweek, att.day_period != 'morning'))

    #     default_value = DummyAttendance(0, 0, 0, 'morning', False)

    #     if resource_calendar_id.two_weeks_calendar:
    #         # find week type of start_date
    #         start_week_type = int(math.floor((self.request_date_from.toordinal() - 1) / 7) % 2)
    #         attendance_actual_week = [att for att in attendances if att.week_type is False or int(att.week_type) == start_week_type]
    #         attendance_actual_next_week = [att for att in attendances if att.week_type is False or int(att.week_type) != start_week_type]
    #         # First, add days of actual week coming after date_from
    #         attendance_filtred = [att for att in attendance_actual_week if int(att.dayofweek) >= self.request_date_from.weekday()]
    #         # Second, add days of the other type of week
    #         attendance_filtred += list(attendance_actual_next_week)
    #         # Third, add days of actual week (to consider days that we have remove first because they coming before date_from)
    #         attendance_filtred += list(attendance_actual_week)

    #         end_week_type = int(math.floor((self.request_date_to.toordinal() - 1) / 7) % 2)
    #         attendance_actual_week = [att for att in attendances if att.week_type is False or int(att.week_type) == end_week_type]
    #         attendance_actual_next_week = [att for att in attendances if att.week_type is False or int(att.week_type) != end_week_type]
    #         attendance_filtred_reversed = list(reversed([att for att in attendance_actual_week if int(att.dayofweek) <= self.request_date_to.weekday()]))
    #         attendance_filtred_reversed += list(reversed(attendance_actual_next_week))
    #         attendance_filtred_reversed += list(reversed(attendance_actual_week))

    #         # find first attendance coming after first_day
    #         attendance_from = attendance_filtred[0]
    #         # find last attendance coming before last_day
    #         attendance_to = attendance_filtred_reversed[0]
    #     else:
    #         # find first attendance coming after first_day
    #         attendance_from = next((att for att in attendances if int(att.dayofweek) >= self.request_date_from.weekday()), attendances[0] if attendances else default_value)
    #         # find last attendance coming before last_day
    #         attendance_to = next((att for att in reversed(attendances) if int(att.dayofweek) <= self.request_date_to.weekday()), attendances[-1] if attendances else default_value)

    #     compensated_request_date_from = self.request_date_from
    #     compensated_request_date_to = self.request_date_to

    #     if self.request_unit_half:
    #         if self.request_date_from_period == 'am':
    #             hour_from = float_to_time(attendance_from.hour_from)
    #             hour_to = float_to_time(attendance_from.hour_to)
    #         else:
    #             hour_from = float_to_time(attendance_to.hour_from)
    #             hour_to = float_to_time(attendance_to.hour_to)
    #     elif self.request_unit_hours:
    #         hour_from = float_to_time(float(self.request_hour_from))
    #         hour_to = float_to_time(float(self.request_hour_to))
    #     elif self.request_unit_custom:
    #         hour_from = self.date_from.time()
    #         hour_to = self.date_to.time()
    #         compensated_request_date_from = self._adjust_date_based_on_tz(self.request_date_from, hour_from)
    #         compensated_request_date_to = self._adjust_date_based_on_tz(self.request_date_to, hour_to)
    #     else:
    #         hour_from = float_to_time(attendance_from.hour_from)
    #         hour_to = float_to_time(attendance_to.hour_to)

    #     tz = 'UTC'  # custom -> already in UTC
    #     # tz = self.env.user.tz if self.env.user.tz and not self.request_unit_custom else 'UTC'  # custom -> already in UTC

    #     date_from = timezone(tz).localize(datetime.combine(compensated_request_date_from, hour_from)).astimezone(UTC).replace(tzinfo=None)
    #     date_to = timezone(tz).localize(datetime.combine(compensated_request_date_to, hour_to)).astimezone(UTC).replace(tzinfo=None)
    #     date_from = date_from - timedelta(hours=8)
    #     date_to = date_to + timedelta(hours=7)
    #     self.update({'date_from': date_from, 'date_to': date_to})
=======
# -*- coding: utf-8 -*-
import logging
import math

from collections import namedtuple

from datetime import datetime, date, timedelta, time
from pytz import timezone, UTC

from odoo import api, fields, models, SUPERUSER_ID, tools
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools.translate import _
from odoo.osv import expression

_logger = logging.getLogger(__name__)

# Used to agglomerate the attendances in order to find the hour_from and hour_to
# See _onchange_request_parameters
DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')
           
class HrLeave(models.Model):
    _inherit = 'hr.leave'


    days_paid = fields.Float(
        string='Dias Pagados', 
        default='0.0'
        
    )

    # @api.onchange('request_date_from_period', 'request_hour_from', 'request_hour_to',
    #               'request_date_from', 'request_date_to',
    #               'employee_id')
    # def _onchange_request_parameters(self):
    #     if not self.request_date_from:
    #         self.date_from = False
    #         return

    #     if self.request_unit_half or self.request_unit_hours:
    #         self.request_date_to = self.request_date_from

    #     if not self.request_date_to:
    #         self.date_to = False
    #         return

    #     resource_calendar_id = self.employee_id.resource_calendar_id or self.env.company.resource_calendar_id
    #     domain = [('calendar_id', '=', resource_calendar_id.id), ('display_type', '=', False)]
    #     attendances = self.env['resource.calendar.attendance'].read_group(domain, ['ids:array_agg(id)', 'hour_from:min(hour_from)', 'hour_to:max(hour_to)', 'week_type', 'dayofweek', 'day_period'], ['week_type', 'dayofweek', 'day_period'], lazy=False)

    #     # Must be sorted by dayofweek ASC and day_period DESC
    #     attendances = sorted([DummyAttendance(group['hour_from'], group['hour_to'], group['dayofweek'], group['day_period'], group['week_type']) for group in attendances], key=lambda att: (att.dayofweek, att.day_period != 'morning'))

    #     default_value = DummyAttendance(0, 0, 0, 'morning', False)

    #     if resource_calendar_id.two_weeks_calendar:
    #         # find week type of start_date
    #         start_week_type = int(math.floor((self.request_date_from.toordinal() - 1) / 7) % 2)
    #         attendance_actual_week = [att for att in attendances if att.week_type is False or int(att.week_type) == start_week_type]
    #         attendance_actual_next_week = [att for att in attendances if att.week_type is False or int(att.week_type) != start_week_type]
    #         # First, add days of actual week coming after date_from
    #         attendance_filtred = [att for att in attendance_actual_week if int(att.dayofweek) >= self.request_date_from.weekday()]
    #         # Second, add days of the other type of week
    #         attendance_filtred += list(attendance_actual_next_week)
    #         # Third, add days of actual week (to consider days that we have remove first because they coming before date_from)
    #         attendance_filtred += list(attendance_actual_week)

    #         end_week_type = int(math.floor((self.request_date_to.toordinal() - 1) / 7) % 2)
    #         attendance_actual_week = [att for att in attendances if att.week_type is False or int(att.week_type) == end_week_type]
    #         attendance_actual_next_week = [att for att in attendances if att.week_type is False or int(att.week_type) != end_week_type]
    #         attendance_filtred_reversed = list(reversed([att for att in attendance_actual_week if int(att.dayofweek) <= self.request_date_to.weekday()]))
    #         attendance_filtred_reversed += list(reversed(attendance_actual_next_week))
    #         attendance_filtred_reversed += list(reversed(attendance_actual_week))

    #         # find first attendance coming after first_day
    #         attendance_from = attendance_filtred[0]
    #         # find last attendance coming before last_day
    #         attendance_to = attendance_filtred_reversed[0]
    #     else:
    #         # find first attendance coming after first_day
    #         attendance_from = next((att for att in attendances if int(att.dayofweek) >= self.request_date_from.weekday()), attendances[0] if attendances else default_value)
    #         # find last attendance coming before last_day
    #         attendance_to = next((att for att in reversed(attendances) if int(att.dayofweek) <= self.request_date_to.weekday()), attendances[-1] if attendances else default_value)

    #     compensated_request_date_from = self.request_date_from
    #     compensated_request_date_to = self.request_date_to

    #     if self.request_unit_half:
    #         if self.request_date_from_period == 'am':
    #             hour_from = float_to_time(attendance_from.hour_from)
    #             hour_to = float_to_time(attendance_from.hour_to)
    #         else:
    #             hour_from = float_to_time(attendance_to.hour_from)
    #             hour_to = float_to_time(attendance_to.hour_to)
    #     elif self.request_unit_hours:
    #         hour_from = float_to_time(float(self.request_hour_from))
    #         hour_to = float_to_time(float(self.request_hour_to))
    #     elif self.request_unit_custom:
    #         hour_from = self.date_from.time()
    #         hour_to = self.date_to.time()
    #         compensated_request_date_from = self._adjust_date_based_on_tz(self.request_date_from, hour_from)
    #         compensated_request_date_to = self._adjust_date_based_on_tz(self.request_date_to, hour_to)
    #     else:
    #         hour_from = float_to_time(attendance_from.hour_from)
    #         hour_to = float_to_time(attendance_to.hour_to)

    #     tz = 'UTC'  # custom -> already in UTC
    #     # tz = self.env.user.tz if self.env.user.tz and not self.request_unit_custom else 'UTC'  # custom -> already in UTC

    #     date_from = timezone(tz).localize(datetime.combine(compensated_request_date_from, hour_from)).astimezone(UTC).replace(tzinfo=None)
    #     date_to = timezone(tz).localize(datetime.combine(compensated_request_date_to, hour_to)).astimezone(UTC).replace(tzinfo=None)
    #     date_from = date_from - timedelta(hours=8)
    #     date_to = date_to + timedelta(hours=7)
    #     self.update({'date_from': date_from, 'date_to': date_to})
>>>>>>> 14b5e054f2a378822e55bbb89100ad6968606a84
    #     self._onchange_leave_dates()