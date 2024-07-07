# -*- coding: utf-8 -*-
##########################################################################
# Author      : Para ti.co SAS
# Copyright(c): 2024-Present ParA TI.CO SAS
# All Rights Reserved.
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
##########################################################################
{
    'name': 'Partner Balance Wizard',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Wizard to calculate partner balances',
    "license":  "Other proprietary",
    'author': 'Para ti.co SAS',
    "website":  "https://www.parati.com.co",
    "description":  "Odoo Partners Trial Balance Wizard",
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/partner_balance_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
}
