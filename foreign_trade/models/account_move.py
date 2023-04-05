from odoo import models, fields,api


class Account_move(models.Model):
    _inherit = 'account.move'
    _description = 'Relacion con Orden de venta'

    sales_order = fields.Many2one(comodel_name='sale.order',compute='compute_sales_order', string='Orden venta')
    export_order = fields.Many2one(comodel_name='x_exportacion',string='Orden exportacion')
    responsible = fields.Many2one(comodel_name='hr.employee', string='Responsable')
    responsible_position = fields.Many2one(comodel_name='hr.job',compute='compute_cargo_responsable',string='Cargo del responsable')



##################################################################
    @api.depends('sales_order')
    def compute_sales_order(self):
        for record in self:
            if record.invoice_origin:
                record.sales_order = self.env['sale.order'].search([('name', '=', record.invoice_origin)])
                record.export_order = record.sales_order.x_studio_exportacion_
                record.x_studio_field_3lEMz = record.sales_order.x_studio_exportacion_
            else:
                record.sales_order = False
#################################################################
    @api.depends('responsible')
    def compute_cargo_responsable(self):
        for record in self:
            if record.responsible:
                record.responsible_position= record.responsible.job_id
            else:
                record.responsible_position = False
