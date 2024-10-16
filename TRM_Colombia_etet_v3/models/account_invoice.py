from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'TRM (USD) Factura'

    trm = fields.Float('TRM', compute = 'compute_trm')

    @api.onchange('invoice_date', 'currency_id')
    def compute_trm(self):
        if self.currency_id.name != "COP" and self.move_type in ['out_invoice','in_invoice']:
            for record in self:
                rates = self.env["res.currency.rate"].sudo().search([("name", "=", record.invoice_date), ("currency_id", "=", record.currency_id.id)])
                if rates:
                    for tasas in rates:
                        if tasas.x_studio_field_rqbWr > 0:
                            record.trm = tasas.x_studio_field_rqbWr
                else:
                    record.trm = 0.0
        else:
            for record in self:
                record.trm = 0.0

