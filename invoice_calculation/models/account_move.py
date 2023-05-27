from odoo import models, fields,api
from datetime import date, timedelta, datetime


class Account_move(models.Model):
    _inherit = 'account.move'
    _description = 'Relacion con Orden de venta'

    flete = fields.Float(string='Flete',compute='compute_flete')
    seguro = fields.Float(string='Seguro',compute='compute_seguro')
    otros = fields.Float(string='Otros',compute='compute_otros')
    numb_line = fields.Integer(string='Numero de lineas', compute='compute_numb_line')
    total_box = fields.Integer(string='Total Cajas', compute='compute_total_box')
    total_units = fields.Integer(string='Total Unidades', compute='compute_total_units')
    total_net = fields.Float(string='Valor Neto', compute='compute_total_net')
    total_net_weight = fields.Integer(string='Total Peso Neto', compute='compute_total_net_weight')
    total_laminated_weight = fields.Integer(string='Total Peso Laminado', compute='compute_total_laminated_weight')
    total_box_weight = fields.Integer(string='Total Peso Caja', compute='compute_total_box_weight')
    total_gross_weight = fields.Integer(string='Total Peso Bruto', compute='compute_total_gross_weight')

    @api.depends('invoice_line_ids')
    def compute_total_units(self):
        for record in self:
            if record.invoice_line_ids:
                total_units = 0
                for t in record.invoice_line_ids:
                    total_units += t.quantity
                record.total_units = total_units
            else:
                record.total_units = 0

    @api.depends('invoice_line_ids')
    def compute_total_box(self):
        for record in self:
            if record.invoice_line_ids:
                total_box = 0
                for t in record.invoice_line_ids:
                    if t.product_id:
                        if t.product_id.x_studio_unidad_de_empaque > 0:
                            total_box += t.quantity / t.product_id.x_studio_unidad_de_empaque
                record.total_box = total_box
            else:
                record.total_box = 0

    @api.depends('invoice_line_ids')
    def compute_total_net(self):
        for record in self:
            if record.invoice_line_ids:
                total_net = 0
                for t in record.invoice_line_ids:
                    total_net += t.subtotal_net
                record.total_net = total_net
            else:
                record.total_net = 0

    @api.depends('invoice_line_ids')
    def compute_total_net_weight(self):
        for record in self:
            if record.invoice_line_ids:
                total_net_weight = 0
                for t in record.invoice_line_ids:
                    total_net_weight += t.net_weight
                record.total_net_weight = round(total_net_weight)
            else:
                record.total_net_weight = 0

    @api.depends('invoice_line_ids')
    def compute_total_laminated_weight(self):
        for record in self:
            if record.invoice_line_ids:
                total_laminated_weight = 0
                for t in record.invoice_line_ids:
                    total_laminated_weight += t.laminated_weight
                record.total_laminated_weight = round(total_laminated_weight)
            else:
                record.total_laminated_weight = 0

    @api.depends('invoice_line_ids')
    def compute_total_box_weight(self):
        for record in self:
            if record.invoice_line_ids:
                total_box_weight = 0
                for t in record.invoice_line_ids:
                    total_box_weight += t.box_weight
                record.total_box_weight = round(total_box_weight)
            else:
                record.total_box_weight = 0

    @api.depends('invoice_line_ids')
    def compute_total_gross_weight(self):
        for record in self:
            record.total_gross_weight = round(record.total_net_weight + record.total_laminated_weight + record.total_box_weight)

    @api.depends('invoice_line_ids')
    def compute_numb_line(self):
        for record in self:
            if record.invoice_line_ids:
                record.numb_line = len(record.invoice_line_ids)
            else:
                record.numb_line = 0

    @api.depends('x_studio_field_3lEMz')
    def compute_flete(self):
        for record in self:
            if record.x_studio_field_3lEMz:
                if record.trm > 0:
                    if record.x_studio_field_3lEMz.x_studio_incoterm_1 == 'DDP':
                        record.flete = (record.x_studio_field_3lEMz.x_studio_flete_origen_cop / record.trm) + record.x_studio_field_3lEMz.x_studio_monto_flete_maritimo_en_usd_1
                    else:
                        record.flete = record.x_studio_field_3lEMz.x_studio_flete_origen_cop / record.trm
                else:
                    record.flete = record.x_studio_field_3lEMz.x_studio_flete_origen_cop
            else:
                record.flete = 0


    @api.depends('x_studio_field_3lEMz')
    def compute_seguro(self):
        for record in self:
            if record.x_studio_field_3lEMz:
                record.seguro = record.x_studio_field_3lEMz.x_studio_monto_seguro_usd_1
            else:
                record.seguro = 0

    @api.depends('x_studio_field_3lEMz')
    def compute_otros(self):
        for record in self:
            if record.x_studio_field_3lEMz:
                if record.trm > 0:
                    if record.x_studio_field_3lEMz.x_studio_incoterm_1 == 'DDP':
                        record.otros = (record.x_studio_field_3lEMz.x_studio_otros_cop / record.trm) + record.x_studio_field_3lEMz.x_studio_otros_gastos_destino_usd
                    else:
                        record.otros = record.x_studio_field_3lEMz.x_studio_otros_cop / record.trm
                else:
                    record.otros = record.x_studio_field_3lEMz.x_studio_otros_cop
            else:
                record.otros = 0

