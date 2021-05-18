# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
           
class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'


    department_id = fields.Many2one('hr.department', string="Departamento empleados")