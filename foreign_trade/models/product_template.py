from odoo import models, fields,api
from datetime import date, timedelta, datetime


class Product_Template(models.Model):
    _inherit = 'product.template'
    _description = 'Campos nuevos productos'

    box_weight = fields.Float(string='Peso de caja',digits='Discount')
    laminated_weight = fields.Float(string='Peso laminado',digits='Product Price')
    x_studio_peso_bruto = fields.Float(string='Peso bruto en Kg',digits='Product Price')
    package_weight = fields.Float(string='Peso paquete',digits='Product Price')
