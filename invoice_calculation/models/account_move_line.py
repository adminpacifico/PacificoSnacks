from odoo import models, fields,api
from datetime import date, timedelta, datetime


class Account_move(models.Model):
    _inherit = 'account.move.line'
    _description = 'Relacion con Orden de venta'


    price_prd = fields.Float(string='Precio Neto', compute='compute_price_prd')
    subtotal_net = fields.Float(string='Subtotal Neto', compute='compute_subtotal_net')
    cost_export = fields.Float(string='Costo exportacion',compute='compute_cost_export')


    @api.depends('price_subtotal')
    def compute_subtotal_net(self):
        for record in self:
            if record.price_subtotal:
                record.subtotal_net = record.price_subtotal - record.cost_export
            else:
                record.subtotal_net = 0


    def compute_price_prd(self):
        for record in self:
            if record.quantity > 0:
                record.price_prd = round((record.subtotal_net / record.quantity), 2)
            else:
                record.price_prd = round((record.subtotal_net), 2)

    @api.depends('move_id')
    def compute_cost_export(self):
        for record in self:
            if record.move_id:
                if record.move_id.numb_line > 0:
                    record.cost_export = (record.move_id.flete + record.move_id.seguro + record.move_id.otros) / record.move_id.numb_line
                else:
                    record.cost_export = (record.move_id.flete + record.move_id.seguro + record.move_id.otros)
            else:
                record.cost_export = 0


