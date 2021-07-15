# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Informe prenomina',
    'version': '1.0',
    'summary': 'Reporte en excel relacion, de novedades de nomina general',
    'description': "reporte en excel relacion, de novedades de nomina general",
    'website': 'https://www.endtoendt.com',
    'depends': ['account', 'hr_payroll_extended'],
    'category': 'Human Resources',
    'author': 'End to End Technology',
    'sequence': 13,
    'demo': [
        
    ],
    'data': [

        'views/prenomina_report_view.xml',

    ],
    'qweb': [

    ],
    'installable': True,
    'auto_install': False,

}
