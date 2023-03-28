# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from datetime import date

class AccountTax(models.Model):
    _inherit = 'account.tax'

    tax_type = fields.Many2one('ln10_co_etet.taxestype', ondelete='set null')


class AccountJournal(models.Model):
    _inherit = "account.journal"

#    handle_book = fields.Boolean(string='Handle Book')
#    selection_book = fields.One2many('selection.book', 'name')

    invoice_resolution = fields.Many2one('account.dian.resolution', 'Resolution Invoice')
    note_resolution = fields.Many2one('account.dian.resolution', 'Credit Note Resolution')

    @api.constrains('invoice_resolution', 'note_resolution')
    def constrain_invoice_resolution(self):
        """Metodo que permite verificar las resoluciones de la dian que no sean iguales"""

        for journal in self:
            if journal.invoice_resolution and journal.note_resolution:
                if journal.invoice_resolution == journal.note_resolution:
                    raise exceptions.ValidationError(_("Invoice resolution and resolution note cant equals"))

class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'localizacion colombia'
    number = fields.Char('Number', compute='_number')
    reverse_concept = fields.Many2one('ln10_co_etet.diancodes', string='Concept dian',
                                      domain=[('type', '=', 'creditnote')])
    resolution_id = fields.Many2one('account.dian.resolution')
    exchange_rate = fields.Float(string='Exchange rate')

    @api.onchange('invoice_date')
    def _number(self):
        for record in self:
            code = record.journal_id.code
            if code != False and record.name != '/':
               numberf = (record.name).split(code)
               record.number = numberf[1]
            else:
                record.number = False

