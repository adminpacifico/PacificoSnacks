# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Reporte de prestaciones',
    'version': '1.0',
    'summary': 'Reporte en excel relacion, de prestaciones de nomina',
    'description': "Reporte en excel relacion, de prestaciones de nomina",
    'website': 'https://www.endtoendt.com',
    'depends': ['account', 'hr_payroll_extended'],
    'category': 'Human Resources',
    'author': 'End to End Technology',
    'sequence': 13,
    'demo': [
        
    ],
    'data': [

        'views/prestaciones_report_view.xml',

    ],
    'qweb': [

    ],
    'installable': True,
    'auto_install': False,

}
