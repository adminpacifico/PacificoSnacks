# -*- coding: utf-8 -*-
# Keware.co / See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang, format_date, get_lang


class MaintenanceEquipment(models.Model):

    _inherit = "maintenance.equipment"

    account_asset_id = fields.Many2one(comodel_name='account.asset', string='Activo')
    account_asset_reference = fields.Char(related='account_asset_id.ref_asset', string='Referencia',readonly=False)
    equipment_code = fields.Char(string='Código de Equipo')

