from odoo import fields, models, api


class AccountPaymentTrm(models.Model):
    _inherit = 'account.payment'
    _description = 'TRM (USD) PAGO'

    trm = fields.Float('TRM', compute = 'compute_trm')

    @api.onchange('payment_date')
    def compute_trm(self):
        for record in self:
            rates = self.env["res.currency.rate"].search([("name", "=", record.payment_date)])
            record.trm = rates.x_studio_field_rqbWr