from odoo import fields, models, api
from odoo.exceptions import ValidationError

class hr_leave_date_extended(models.Model):
    _name = 'hr.leave.date_extended'
    _description = 'Fechas de ausencia extendidas'

    date_from = fields.Date('Fecha inicial')
    date_to = fields.Date('Fecha final')
    #leave_id = fields.One2many('hr.leave', 'date_extended_id', string='Ausencia')
    leave_id = fields.Many2one('hr.leave', string='Ausencia')












