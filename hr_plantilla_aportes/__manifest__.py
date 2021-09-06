# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'plantilla aportes en linea',
    'version': '1.0',
    'summary': 'summarys',
    'description': "reporte para pago seguridad social aportes en linea",
    'website': 'https://www.endtoendt.com',
    'depends': ['account', 'hr_payroll_extended'],
    'category': 'category',
    'author': 'Enrrique Aguiar Endtoendt technologys sas',
    'sequence': 13,
    'demo': [
        
    ],
    'data': [

        'views/plantilla_report_view.xml',

    ],
    'qweb': [

    ],
    'installable': True,
    'auto_install': False,

}
