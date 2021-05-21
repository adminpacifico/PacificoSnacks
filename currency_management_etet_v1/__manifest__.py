# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Divisas',
    'version': '1.0',
    'summary': 'summary',
    'description': "reporte generado en excel para calculo de divisas en exportaciones",
    'website': 'https://www.endtoendt.com',
    'depends': ['account', 'account_reports'],
    'category': 'category',
    'author': 'Enrrique Aguiar',
    'sequence': 13,
    'demo': [
        
    ],
    'data': [

        'views/currency_management.xml',

    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
