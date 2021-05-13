from odoo import fields, models, api


class HrContractreport(models.Model):
    _inherit = 'hr.contract'
    _description = 'adicion campo tipo de contratos'

    contract_type = fields.Many2many('hr.contract')
