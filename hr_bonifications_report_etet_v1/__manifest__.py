# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Bonificaciones empleado',
    'version': '1.0',
    'summary': 'summarys',
    'description': "reporte de bonificaciones",
    'website': 'https://www.endtoendt.com',
    'depends': ['hr_payroll_extended'],
    'category': 'category',
    'author': 'Enrrique Aguiar',
    'sequence': 13,
    'demo': [
        
    ],
    'data': [

        'views/bonifications_report_view.xml',

    ],
    'qweb': [

    ],
    'installable': True,
    'auto_install': False,

}
