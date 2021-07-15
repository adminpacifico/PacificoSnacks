# -*- coding: utf-8 -*-
from datetime import date, datetime, time, timedelta

import babel
from dateutil.relativedelta import relativedelta
from pytz import timezone

from odoo.tools import float_round, date_utils
from odoo.tools.misc import format_date
from odoo.tools.safe_eval import safe_eval

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, AccessError, ValidationError

import base64
from dateutil.relativedelta import relativedelta
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips
from odoo.exceptions import UserError, ValidationError

class HrPayslipLine(models.Model):
    _name = "hr.payslip.line"
    _inherit = "hr.payslip.line"
    _description = "Payslip Line"

    amount = fields.Float(digits=(0, 5))
    rate = fields.Float(string='Rate (%)', digits=(0, 2), default=100.0)

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):
        for line in self:
             line.total = float(line.quantity) * line.amount * line.rate / 100


