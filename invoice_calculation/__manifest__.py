# -*- coding: utf.8 -*-
{
    'name': 'invoice_calculation ',
    'version': '1.0',
    'summary': 'Modulo contabilidad/factura',
    'description': 'Campos adicionales para realizar calculo en la Factura de venta',
    'category': 'Trade',
    'website': 'https://www.endtoendt.com/',
    'author': 'End to End Technology',
    'depends': ['base', 'account','hr','sale'],
    'data': [

        'security/ir.model.access.csv',
        'views/account_move_view.xml',


    ],
    'demo': [],
    'application': True,
    'installable': True,
    'auto_install': False
}
