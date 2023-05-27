from odoo import models, fields,api
from datetime import date, timedelta, datetime


class Stock_Picking(models.Model):
    _inherit = 'stock.picking'
    _description = 'Relacion con Orden de venta'


    total_net_weight_oc = fields.Integer(string='Total Peso Neto',compute='compute_total_net_weight_oc')
    total_laminated_weight_oc = fields.Integer(string='Total Peso Laminado', compute='compute_total_laminated_weight_oc')
    total_box_weight_oc = fields.Integer(string='Total Peso Caja', compute='compute_total_box_weight_oc')
    total_gross_weight_oc = fields.Integer(string='Total Peso Bruto', compute= 'compute_total_gross_weight_oc')
    total_box_oc = fields.Integer(string='Total Cajas', compute='compute_total_box_oc')

    @api.depends('move_line_ids_without_package')
    def compute_total_box_oc(self):
        for record in self:
            if record.move_line_ids_without_package:
                total_box = 0
                for t in record.move_line_ids_without_package:
                    if t.product_id:
                        if t.product_id.x_studio_unidad_de_empaque > 0:
                            total_box += t.qty_done / t.product_id.x_studio_unidad_de_empaque
                record.total_box_oc = total_box
            else:
                record.total_box_oc = 0


    @api.depends('move_line_ids_without_package')
    def compute_total_laminated_weight_oc(self):
        for record in self:
            if record.move_line_ids_without_package:
                total_laminated_weight_oc = 0
                for t in record.move_line_ids_without_package:
                    total_laminated_weight_oc += t.laminated_weight_oc
                record.total_laminated_weight_oc = round(total_laminated_weight_oc)
            else:
                record.total_laminated_weight_oc = 0

    @api.depends('move_line_ids_without_package')
    def compute_total_net_weight_oc(self):
        for record in self:
            if record.move_line_ids_without_package:
                total_net_weight_oc = 0
                for t in record.move_line_ids_without_package:
                    total_net_weight_oc += t.net_weight_oc
                record.total_net_weight_oc = round(total_net_weight_oc)
            else:
                record.total_net_weight_oc = 0


    @api.depends('move_line_ids_without_package')
    def compute_total_box_weight_oc(self):
        for record in self:
            if record.move_line_ids_without_package:
                total_box_weight_oc = 0
                for t in record.move_line_ids_without_package:
                    total_box_weight_oc += t.box_weight_oc
                record.total_box_weight_oc = round(total_box_weight_oc)
            else:
                record.total_box_weight_oc = 0

    @api.depends('move_line_ids_without_package')
    def compute_total_gross_weight_oc(self):
        for record in self:
            record.total_gross_weight_oc = round(record.total_net_weight_oc + record.total_laminated_weight_oc + record.total_box_weight_oc)


