from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'TRM (USD) Factura'

    trm = fields.Float('TRM', compute = 'compute_trm')

    @api.onchange('invoice_date', 'currency_id')
    def compute_trm(self):
        for record in self:
            rates = self.env["res.currency.rate"].search([("name", "=", record.invoice_date), ("currency_id", "=", record.currency_id.id)])
            for rate in rates:
                if rate.x_studio_field_rqbWr != 0:
                    record.trm = rate.x_studio_field_rqbWr
