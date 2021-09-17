# -*- coding: utf-8 -*-
from datetime import date, datetime, time, timedelta

import babel
from dateutil.relativedelta import relativedelta
from pytz import timezone

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, AccessError, ValidationError

           
class Account(models.Model):
    _inherit = 'account.account'

    blocking_analytic_payroll = fields.Boolean(string="Bloqueo Analítico Nomina", default=False)