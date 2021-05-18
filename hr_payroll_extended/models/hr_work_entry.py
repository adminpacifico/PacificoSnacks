# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from contextlib import contextmanager
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from datetime import datetime
from datetime import timedelta
import time
import datetime

class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'


    @api.depends('date_stop', 'date_start')
    def _compute_duration(self):
        for work_entry in self:
            work_entry.duration = work_entry._get_duration(work_entry.date_start, work_entry.date_stop)


    def _get_duration(self, date_start, date_stop):
        if not date_start or not date_stop:
            return 0
        dt = date_stop - date_start
        lim_day = timedelta(hours=8)
        if dt <= lim_day:
            return dt.total_seconds()/3600.
        else:
            return (dt.days+1) * 8  # Number of hours
        # return dt.days * 8 + dt.seconds / 3600  # Number of hours
        # return (dt.days+1) * 8  # Number of hours


    def _inverse_duration(self):
        for work_entry in self:
            if work_entry.date_start and work_entry.duration:
                print('--')
                # work_entry.date_stop = work_entry.date_start + relativedelta(hours=work_entry.duration)