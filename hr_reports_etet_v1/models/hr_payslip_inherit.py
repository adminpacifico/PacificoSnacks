# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError
import time
from datetime import datetime, timedelta
import xlwt
import base64
# from cStringIO import StringIO
from io import StringIO
from io import BytesIO
import xlsxwriter
import types
import logging

_logger = logging.getLogger(__name__)


class HrPayslipInherit(models.Model):
    _inherit = 'hr.payslip'
    _description = 'adicion campo de observaciones para el volante de pago'


    observaciones = fields.Char(string="Observaciones")
    lineas = line_ids = fields.One2many('hr.payslip.line', 'slip_id', string='Payslip Lines', readonly=True,
        states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})

    def make_file(self):
        _logger.error("INICIA LA FUNCIÓN CONSTRUIR EL ARCHIVO ")


    def action_print_payslip(self):

        return {
            'name': 'Payslip',
            'type': 'ir.actions.act_url',
            'url': '/print/payslips?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x) for x in self.ids)},
        }