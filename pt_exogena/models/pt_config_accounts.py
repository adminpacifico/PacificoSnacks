# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class PtConfigAccounts(models.Model):
    _name = 'pt.config.accounts'
    _description = 'Pt Config Accounts'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    pt_config_account_line_ids = fields.One2many(comodel_name='pt.config.accounts.concepts', inverse_name='pt_config_accounts_id', string='Account Lines')


class PtConfigAccountsConcepts(models.Model):
    _name = 'pt.config.accounts.concepts'
    _description = 'Pt Config Accounts Concepts'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    pt_config_accounts_id = fields.Many2one(comodel_name='pt.config.accounts', string='Pt Config Accounts')
    pt_config_accounts_concepts_line_ids = fields.One2many(comodel_name='pt.config.accounts.concepts.lines',
                                                           inverse_name='pt_config_accounts_concepts_id',
                                                           string='Concepts Lines')


class PtConfigAccountsConceptsLines(models.Model):
    _name = 'pt.config.accounts.concepts.lines'
    _description = 'Pt Config Accounts Concepts Lines'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    account_id = fields.Many2one(comodel_name='account.account', string='Account', required=True)
    column_number = fields.Integer(string='Column Number', required=True)
    calculation_type = fields.Selection(selection=[('sumd', 'Sum Debits'), ('sumc', 'Sum Credits'),
                                                   ('balance', 'Balance')], string='Calculation Type', required=True)
    pt_config_accounts_concepts_id = fields.Many2one(comodel_name='pt.config.accounts.concepts',
                                                     string='Pt Config Accounts Concepts')
