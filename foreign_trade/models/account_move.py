from odoo import models, fields,api
from datetime import date, timedelta, datetime


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
                if record.move_type == 'out_invoice':
                    order_origin = self.env['sale.order'].search([('name', '=', record.invoice_origin)])
                    if order_origin:
                        record.sales_order = order_origin
                        record.export_order = record.sales_order.x_studio_exportacion_
                        record.x_studio_field_3lEMz = record.sales_order.x_studio_exportacion_
                        if record.invoice_date_due and not record.invoice_payment_term_id:
                            record.x_studio_fecha_de_vencimiento = record.invoice_date_due
                        else:
                            if record.sales_order.possible_arrival_date_destination:
                                if record.invoice_payment_term_id.line_ids:
                                    dias =  timedelta(days=record.invoice_payment_term_id.line_ids.days)
                                else:
                                    dias = 0
                                record.x_studio_fecha_de_vencimiento = record.sales_order.possible_arrival_date_destination + dias
                            else:
                                record.x_studio_fecha_de_vencimiento = False
                else:
                    record.sales_order = False
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
