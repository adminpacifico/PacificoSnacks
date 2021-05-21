# -*- coding: utf-8 -*-
from datetime import date, datetime, time, timedelta

import babel
from dateutil.relativedelta import relativedelta
from pytz import timezone

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, AccessError, ValidationError

           
class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'


    tag_id = fields.Many2one('account.analytic.tag', string="Etiqueta")