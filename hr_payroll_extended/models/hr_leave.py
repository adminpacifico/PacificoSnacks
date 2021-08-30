# -*- coding: utf-8 -*-
import logging
import math
from collections import defaultdict
from datetime import datetime, date

from odoo import api, fields, models, _
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

def days360(s, e):
    return ( ((e.year * 12 + e.month) * 30 + e.day) - ((s.year * 12 + s.month) * 30 + s.day))

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    contract_id = fields.Many2one('hr.contract', string='Contracto', track_visibility='onchange')
    days_paid = fields.Float(string='Dias Pagados', default='0.0')
    days_vacations = fields.Integer(string="Vacaciones Disponibles", compute='get_days_vacations')
    holiday_status_name = fields.Char(string="Nombre de ausencia", compute='get_holiday_status_name')
    amount_vacations = fields.Float(string="Valor Pagado")
    workday = fields.Float(string="Días Hábiles", default=0)
    holiday = fields.Float(string="Días Festivos", default=0)
    manual_data = fields.Boolean(string="Carga Manual", default=False)

    date_extended = fields.Boolean(string="Extensión de incapacidad", default=False)
    #date_extended_id = fields.Many2one('hr.leave.date_extended', string='Historial de Extensión')
    date_extended_id = fields.One2many('hr.leave.date_extended', 'leave_id', string='Historial de Extensión')
    #date_extended_id = fields.Many2many('hr.leave.date_extended', 'leave_id', string='Historial de Extensión')

    amount_license = fields.Float(string="Base para pago")

    @api.onchange('date_from', 'date_to', 'employee_id', 'holiday_status_id', 'number_of_days')
    def get_amount_license(self):
        for record in self:
            contracts = record.env['hr.contract'].search([('employee_id', '=', record.employee_id.id),('state','=','open')])
            if contracts and record.holiday_status_id.name == 'Licencia de Maternidad' or contracts and record.holiday_status_id.name == 'Licencia de Paternidad':
                for contract in contracts:
                    salary = contract.wage
                    total_extra_hour = 0
                    amountb = 0
                    amountc = 0
                    date_from = str(record.date_from)
                    date_to = str(record.date_from)
                    date_to = dateutil.parser.parse(date_to).date()
                    date_from = dateutil.parser.parse(date_from).date()

                    horas_extras_12month_before = record.env['hr.payslip'].get_inputs_hora_extra_12month_before(contract, date_from, date_to)
                    if horas_extras_12month_before:
                        hm12_date_ini = date_to - relativedelta(months=12)
                        hm12_date_ini = hm12_date_ini + relativedelta(days=1)
                        if contract.date_start <= hm12_date_ini:
                            hm12_date_init = hm12_date_ini
                        else:
                            hm12_date_init = contract.date_start
                        # total_days12y = days_between(hm12_date_init, date_to)
                        if date_to.day == 31:
                            date_to = date_to - relativedelta(days=1)
                        total_days12y = days360(hm12_date_init, date_to) + 1

                        if total_days12y < 30:
                            day_base = total_days12y
                        else:
                            day_base = 30

                        extradiurna_amount = 0
                        extradiurnafestivo_amount = 0
                        extranocturna_amount = 0
                        extranocturnafestivo_amount = 0
                        recargonocturno_amount = 0
                        recargodiurnofestivo_amount = 0
                        recargonocturnofestivo_amount = 0
                        for hora in horas_extras_12month_before:
                            if hora[1] == 'EXTRADIURNA':
                                extradiurna_amount = extradiurna_amount + hora[2]
                            if hora[1] == 'EXTRADIURNAFESTIVO':
                                extradiurnafestivo_amount = extradiurnafestivo_amount + hora[2]
                            if hora[1] == 'EXTRANOCTURNA':
                                extranocturna_amount = extranocturna_amount + hora[2]
                            if hora[1] == 'EXTRANOCTURNAFESTIVO':
                                extranocturnafestivo_amount = extranocturnafestivo_amount + hora[2]
                            if hora[1] == 'RECARGONOCTURNO':
                                recargonocturno_amount = recargonocturno_amount + hora[2]
                            if hora[1] == 'RECARGODIURNOFESTIVO':
                                recargodiurnofestivo_amount = recargodiurnofestivo_amount + hora[2]
                            if hora[1] == 'RECARGONOCTURNOFESTIVO':
                                recargonocturnofestivo_amount = recargonocturnofestivo_amount + hora[2]

                        if not extradiurna_amount == 0:
                            extradiurna_amount = (extradiurna_amount / total_days12y) * day_base
                        if not extradiurnafestivo_amount == 0:
                            extradiurnafestivo_amount = (extradiurnafestivo_amount / total_days12y) * day_base
                        if not extranocturna_amount == 0:
                            extranocturna_amount = (extranocturna_amount / total_days12y) * day_base
                        if not extranocturnafestivo_amount == 0:
                            extranocturnafestivo_amount = (extranocturnafestivo_amount / total_days12y) * day_base
                        if not recargonocturno_amount == 0:
                            recargonocturno_amount = (recargonocturno_amount / total_days12y) * day_base
                        if not recargodiurnofestivo_amount == 0:
                            recargodiurnofestivo_amount = (recargodiurnofestivo_amount / total_days12y) * day_base
                        if not recargonocturnofestivo_amount == 0:
                            recargonocturnofestivo_amount = (recargonocturnofestivo_amount / total_days12y) * day_base

                        total_extra_hour = extradiurna_amount + extradiurnafestivo_amount + extranocturna_amount + extranocturnafestivo_amount + recargonocturno_amount + recargodiurnofestivo_amount + recargonocturnofestivo_amount

                    inputs_loans_12month_before = record.env['hr.payslip'].get_inputs_loans_12month_before(contract, date_from, date_to)
                    if inputs_loans_12month_before:
                        lm12_date_ini = date_to - relativedelta(months=12)
                        lm12_date_ini = lm12_date_ini + relativedelta(days=1)
                        if contract.date_start <= lm12_date_ini:
                            lm12_date_init = lm12_date_ini
                        else:
                            lm12_date_init = contract.date_start
                        # total_dayl12 = days_between(lm12_date_init, date_to)
                        if date_to.day == 31:
                            date_to = date_to - relativedelta(days=1)
                        total_dayl12 = days360(lm12_date_init, date_to) + 1
                        if total_dayl12 < 30:
                            day_base = total_dayl12
                        else:
                            day_base = 30
                        amountb = 0
                        amountc = 0
                        for loans in inputs_loans_12month_before:
                            if loans[1] == 'BONIFICACION':
                                amountb = amountb + loans[2]
                            if loans[1] == 'COMISION':
                                amountc = amountc + loans[2]
                        if not amountb == 0:
                            amountb = (amountb / total_dayl12) * day_base
                        if not amountc == 0:
                            amountc = (amountc / total_dayl12) * day_base

                    record.amount_license = round((salary + total_extra_hour + amountb + amountc))
            else:
                record.amount_license = 0

    @api.onchange('employee_id')
    def onchange_employee(self):
        for record in self:
            if record.employee_id:
                contract = self.env["hr.contract"].search(
                    [('employee_id', '=', record.employee_id.id), ('state', '=', 'open')], limit=1)
                if contract:
                    record.contract_id = contract.id
                else:
                    raise UserError(_('El empleado no tiene un contracto.'))

    @api.onchange('date_from', 'date_to', 'employee_id','number_of_days')
    def get_holiday(self):
        for record in self:
            if record.employee_id:
                calendar = record.employee_id.resource_calendar_holidays_id
                holidays = record.employee_id._get_work_days_data_batch(record.date_from, record.date_to, calendar=calendar)[record.employee_id.id]
                record.workday = holidays['days']
                record.holiday = record.number_of_days - record.workday
                if record.holiday_status_id.name == 'Vacaciones en dinero' or record.holiday_status_id.name == 'Vacaciones en dinero a liquidar':
                    record.workday = record.number_of_days
                    record.holiday = 0

    @api.onchange('holiday_status_id')
    def get_holiday_status_name(self):
        for record in self:
            record.holiday_status_name = record.holiday_status_id.name

    def get_days_vacations(self):
        for record in self:
            contracts = record.env['hr.contract'].search([('employee_id', '=', record.employee_id.id),('state','=','open')])
            if contracts:
                for contract in contracts:
                    record.days_vacations = contract.vacations_available
            else:
                record.days_vacations = 0

    @api.onchange('date_from','date_to','employee_id','holiday_status_id','number_of_days')
    def get_amount_vacations(self):
        for record in self:
            if record.holiday_status_id.name == 'Vacaciones en dinero':
                record.request_date_to = record.date_from
                record.date_to = record.date_from
            contracts = record.env['hr.contract'].search([('employee_id', '=', record.employee_id.id),('state','=','open')])
            if record.manual_data == False:
                if contracts and record.holiday_status_id.name == 'Vacaciones' or contracts and record.holiday_status_id.name == 'Vacaciones a liquidar'or contracts and record.holiday_status_id.name == 'Vacaciones en dinero' or contracts and record.holiday_status_id.name == 'Vacaciones en dinero a liquidar':
                    for contract in contracts:
                        salary = contract.wage
                        total_extra_hour = 0
                        amountb = 0
                        amountc = 0
                        date_from = str(record.date_from)
                        date_from = dateutil.parser.parse(date_from).date()
                        date_to = str(record.date_to)
                        date_to = dateutil.parser.parse(date_to).date()

                        if date_to.day <= 15:
                            date_to = date(date_to.year, date_to.month, 15)

                        if date_to.day > 15 and date_to.day <= 31:
                            date_to = date(date_to.year, date_to.month, 30)

                        horas_extras_12month_before = record.env['hr.payslip'].get_inputs_hora_extra_12month_before(contract, date_from, date_to)
                        if horas_extras_12month_before:
                            hm12_date_ini = date_to - relativedelta(months=12)
                            hm12_date_ini = hm12_date_ini + relativedelta(days=1)
                            if contract.date_start <= hm12_date_ini:
                                hm12_date_init = hm12_date_ini
                            else:
                                hm12_date_init = contract.date_start
                            # total_days12y = days_between(hm12_date_init, date_to)
                            if date_to.day == 31:
                                date_to = date_to - relativedelta(days=1)
                            total_days12y = days360(hm12_date_init, date_to) + 1

                            if total_days12y < 30:
                                day_base = total_days12y
                            else:
                                day_base = 30

                            extradiurna_amount = 0
                            extradiurnafestivo_amount = 0
                            extranocturna_amount = 0
                            extranocturnafestivo_amount = 0
                            recargonocturno_amount = 0
                            recargodiurnofestivo_amount = 0
                            recargonocturnofestivo_amount = 0
                            for hora in horas_extras_12month_before:
                                if hora[1] == 'EXTRADIURNA':
                                    extradiurna_amount = extradiurna_amount + hora[2]
                                if hora[1] == 'EXTRADIURNAFESTIVO':
                                    extradiurnafestivo_amount = extradiurnafestivo_amount + hora[2]
                                if hora[1] == 'EXTRANOCTURNA':
                                    extranocturna_amount = extranocturna_amount + hora[2]
                                if hora[1] == 'EXTRANOCTURNAFESTIVO':
                                    extranocturnafestivo_amount = extranocturnafestivo_amount + hora[2]
                                if hora[1] == 'RECARGONOCTURNO':
                                    recargonocturno_amount = recargonocturno_amount + hora[2]
                                if hora[1] == 'RECARGODIURNOFESTIVO':
                                    recargodiurnofestivo_amount = recargodiurnofestivo_amount + hora[2]
                                if hora[1] == 'RECARGONOCTURNOFESTIVO':
                                    recargonocturnofestivo_amount = recargonocturnofestivo_amount + hora[2]

                            if not extradiurna_amount == 0:
                                extradiurna_amount = (extradiurna_amount / total_days12y) * day_base
                            if not extradiurnafestivo_amount == 0:
                                extradiurnafestivo_amount = (extradiurnafestivo_amount / total_days12y) * day_base
                            if not extranocturna_amount == 0:
                                extranocturna_amount = (extranocturna_amount / total_days12y) * day_base
                            if not extranocturnafestivo_amount == 0:
                                extranocturnafestivo_amount = (extranocturnafestivo_amount / total_days12y) * day_base
                            if not recargonocturno_amount == 0:
                                recargonocturno_amount = (recargonocturno_amount / total_days12y) * day_base
                            if not recargodiurnofestivo_amount == 0:
                                recargodiurnofestivo_amount = (recargodiurnofestivo_amount / total_days12y) * day_base
                            if not recargonocturnofestivo_amount == 0:
                                recargonocturnofestivo_amount = (recargonocturnofestivo_amount / total_days12y) * day_base

                            total_extra_hour = extradiurna_amount + extradiurnafestivo_amount + extranocturna_amount + extranocturnafestivo_amount + recargonocturno_amount + recargodiurnofestivo_amount + recargonocturnofestivo_amount

                        inputs_loans_12month_before = record.env['hr.payslip'].get_inputs_loans_12month_before(contract, date_from, date_to)
                        if inputs_loans_12month_before:
                            lm12_date_ini = date_to - relativedelta(months=12)
                            lm12_date_ini = lm12_date_ini + relativedelta(days=1)
                            if contract.date_start <= lm12_date_ini:
                                lm12_date_init = lm12_date_ini
                            else:
                                lm12_date_init = contract.date_start
                            # total_dayl12 = days_between(lm12_date_init, date_to)
                            if date_to.day == 31:
                                date_to = date_to - relativedelta(days=1)
                            total_dayl12 = days360(lm12_date_init, date_to) + 1
                            if total_dayl12 < 30:
                                day_base = total_dayl12
                            else:
                                day_base = 30
                            amountb = 0
                            amountc = 0
                            for loans in inputs_loans_12month_before:
                                if loans[1] == 'BONIFICACION':
                                    amountb = amountb + loans[2]
                                if loans[1] == 'COMISION':
                                    amountc = amountc + loans[2]
                            if not amountb == 0:
                                amountb = (amountb / total_dayl12) * day_base
                            if not amountc == 0:
                                amountc = (amountc / total_dayl12) * day_base

                        record.amount_vacations = round((((salary + total_extra_hour + amountb + amountc)/30) * record.number_of_days))
                else:
                    record.amount_vacations = 0

    def write(self, values):
        if values.get('number_of_days'):
            duration_vac= values.get('number_of_days')
        else:
            duration_vac = self.number_of_days

        if self.holiday_status_id.name == 'Vacaciones en dinero' and  7 < duration_vac :
            raise Warning('¡No es posible registrar la ausencia! Solo se puede solicitar un máximo de 7 días')
        return super(HrLeave, self).write(values)

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

    def _cancel_work_entry_conflict(self):
        """
        Creates a leave work entry for each hr.leave in self.
        Check overlapping work entries with self.
        Work entries completely included in a leave are archived.
        e.g.:
            |----- work entry ----|---- work entry ----|
                |------------------- hr.leave ---------------|
                                    ||
                                    vv
            |----* work entry ****|
                |************ work entry leave --------------|
        """

        if not self:
            return

        if self.holiday_status_id.name == 'Vacaciones en dinero' or self.holiday_status_id.name == 'Vacaciones en dinero a liquidar':
            return
        # 1. Create a work entry for each leave
        work_entries_vals_list = []
        for leave in self:
            contracts = leave.employee_id.sudo()._get_contracts(leave.date_from, leave.date_to, states=['open', 'close'])
            for contract in contracts:
                # Generate only if it has aleady been generated
                if leave.date_to >= contract.date_generated_from and leave.date_from <= contract.date_generated_to:
                    work_entries_vals_list += contracts._get_work_entries_values(leave.date_from, leave.date_to)

        new_leave_work_entries = self.env['hr.work.entry'].create(work_entries_vals_list)

        if new_leave_work_entries:
            # 2. Fetch overlapping work entries, grouped by employees
            start = min(self.mapped('date_from'), default=False)
            stop = max(self.mapped('date_to'), default=False)
            work_entry_groups = self.env['hr.work.entry'].read_group([
                ('date_start', '<', stop),
                ('date_stop', '>', start),
                ('employee_id', 'in', self.employee_id.ids),
            ], ['work_entry_ids:array_agg(id)', 'employee_id'], ['employee_id', 'date_start', 'date_stop'], lazy=False)
            work_entries_by_employee = defaultdict(lambda: self.env['hr.work.entry'])
            for group in work_entry_groups:
                employee_id = group.get('employee_id')[0]
                work_entries_by_employee[employee_id] |= self.env['hr.work.entry'].browse(group.get('work_entry_ids'))

            # 3. Archive work entries included in leaves
            included = self.env['hr.work.entry']
            overlappping = self.env['hr.work.entry']
            for work_entries in work_entries_by_employee.values():
                # Work entries for this employee
                new_employee_work_entries = work_entries & new_leave_work_entries
                previous_employee_work_entries = work_entries - new_leave_work_entries

                # Build intervals from work entries
                leave_intervals = new_employee_work_entries._to_intervals()
                conflicts_intervals = previous_employee_work_entries._to_intervals()

                # Compute intervals completely outside any leave
                # Intervals are outside, but associated records are overlapping.
                outside_intervals = conflicts_intervals - leave_intervals

                overlappping |= self.env['hr.work.entry']._from_intervals(outside_intervals)
                included |= previous_employee_work_entries - overlappping
            overlappping.write({'leave_id': False})
            included.write({'active': False})