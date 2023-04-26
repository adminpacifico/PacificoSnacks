# -*- coding: utf.8 -*-
{
    'name': 'Comercio Exterior',
    'version': '1.0',
    'summary': 'Modulo comercio exterior',
    'description': 'Modulo comercio exterior',
    'category': 'Trade',
    'website': 'https://www.endtoendt.com/',
    'author': 'End to End Technology',
    'depends': ['base', 'account','hr','sale'],
    'data': [

        'security/ir.model.access.csv',
        #'views/sales_order_view.xml',
        'views/infoexport_view.xml',
        'views/account_move_view.xml',
        'views/stock_picking_view.xml',
        'views/res_partner_view.xml',
        'views/product_template_view.xml',



    ],
    'demo': [],
    'application': True,
    'installable': True,
    'auto_install': False
}
