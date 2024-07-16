# -*- coding: utf-8 -*-
# developed by Para ti.co SAS 2024 by Cesar Ortiz

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    sale_advance_account_id = fields.Many2one("account.account", string="Sale Advance Account", domain="[('deprecated', '=', False)]")
    purchase_advance_account_id = fields.Many2one("account.account", string="Purchase Advance Account", domain="[('deprecated', '=', False)]")
