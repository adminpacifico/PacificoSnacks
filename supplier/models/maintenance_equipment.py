# -*- coding: utf-8 -*-
# Keware.co / See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang, format_date, get_lang


class MaintenanceEquipment(models.Model):

    _inherit = "maintenance.equipment"
    supplier_ids = fields.One2many('product.supplierinfo', 'maintenance_equipment_id', 'Proveedor', help="Define vendor pricelists.")

