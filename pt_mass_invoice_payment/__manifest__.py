# -*- coding: utf-8 -*-
#
# You should have received a copy of the GNU Lesser General Public License
#
# email: administracion@parati.com.co

{
    'name': 'PT Mass Invoice Payment',
    'summary': 'Mass invoice and bill payment wizard',
    'description': "Advance payments AR and AP",
    'author': "Para TI.CO SAS",
    'license': "LGPL-3",
    'category': 'Finance',
    'version': '17.0',
    'depends': [
        'base',
        'account',
        'account_payment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_invoice_payment_views.xml',
    ],
    'installable': True,
    'application': True,
}