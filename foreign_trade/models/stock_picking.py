from odoo import models, fields,api


class Stock_picking(models.Model):
    _inherit = 'stock.picking'
    _description = 'Campos adicionales ventas'

    sale_order_id = fields.Many2one(comodel_name='sale.order',compute='compute_sale_order_id', string='Orden venta')

    @api.depends('sale_order_id')
    def compute_sale_order_id(self):
        for record in self:
            if record.origin:
                record.sale_order_id = self.env['sale.order'].search([('name', '=', record.origin)])
                record.x_studio_exportacion_ = record.sale_order_id.x_studio_exportacion_
            else:
                record.sale_order = False







