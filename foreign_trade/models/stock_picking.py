from odoo import models, fields,api


class Stock_picking(models.Model):
    _inherit = 'stock.picking'
    _description = 'Campos adicionales ventas'

    sale_order_id = fields.Many2one(comodel_name='sale.order',compute='compute_sale_order_id', string='Orden venta')
    #factura_order_id = fields.Many2one(comodel_name='account.move', compute='compute_factura_order_id', string='Factura')

    @api.depends('sale_order_id')
    def compute_sale_order_id(self):
        for record in self:
            if record.origin:
                record.sale_order_id = self.env['sale.order'].search([('name', '=', record.origin)])
                record.x_studio_exportacion_ = record.sale_order_id.x_studio_exportacion_
            else:
                record.sale_order_id = False

    @api.depends('factura_order_id')
    def compute_factura_order_id(self):
        for record in self:
            if record.x_studio_exportacion_:
                record.factura_order_id = record.x_studio_exportacion_.x_studio_factura__1
            else:
                record.factura_order_id = False









