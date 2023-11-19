# -*- coding: utf-8 -*-
# Keware.co / See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang, format_date, get_lang


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    maintenance_equipment_id = fields.Many2one(comodel_name='maintenance.equipment', string="Equipo de mantenimiento")


