from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'
    _description = 'Campos adicionales contactos'

    email_alterno = fields.Char(string='Correo certificado de origen')


