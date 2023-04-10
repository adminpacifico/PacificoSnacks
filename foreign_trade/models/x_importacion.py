from odoo import models, fields, api


class Importacion(models.Model):
    #_inherit = 'x_exportacion'
    _name = 'x_importacion'
    _description = 'actualizacion campos exportacion'
    _rec_name = 'x_name'



    prueba = fields.Char(string='Prueba')

