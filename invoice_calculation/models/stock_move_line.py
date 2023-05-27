from odoo import models, fields,api
from datetime import date, timedelta, datetime


class Stock_move_line(models.Model):
    _inherit = 'stock.move.line'
    _description = 'Relacion con Orden de venta'

    net_weight_oc = fields.Float(string='Peso Neto',compute='compute_net_weight_oc')
    laminated_weight_oc = fields.Float(string='Peso Laminado', compute = 'compute_laminated_weight_oc')
    box_weight_oc = fields.Float(string='Peso Caja', compute='compute_box_weight_oc')

    @api.depends('product_id')
    def compute_laminated_weight_oc(self):
        for record in self:
            if record.product_id:
                record.laminated_weight_oc = record.product_id.laminated_weight * record.qty_done
            else:
                record.laminated_weight_oc = 0

    @api.depends('product_id')
    def compute_net_weight_oc(self):
        for record in self:
            if record.product_id:
                record.net_weight_oc = record.product_id.package_weight * record.qty_done
            else:
                record.net_weight_oc = 0

    @api.depends('product_id')
    def compute_box_weight_oc(self):
        for record in self:
            if record.product_id:
                if record.product_id.x_studio_unidad_de_empaque > 0:
                    record.box_weight_oc = record.product_id.box_weight * (record.qty_done/record.product_id.x_studio_unidad_de_empaque)
                else:
                    record.box_weight_oc = 0
            else:
                record.box_weight_oc = 0

