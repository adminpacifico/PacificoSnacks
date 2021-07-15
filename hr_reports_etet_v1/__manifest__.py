# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'volante de nomina',
    'version': '1.0',
    'summary': 'Reporte de nomina liquidacion de contrato y volante de nomina',
    'description': "Reporte de nomina liquidacion de contrato y volante de nomina",
    'website': 'https://www.endtoendt.com',
    'depends': ['hr_payroll_extended'],
    'category': 'Human Resources',
    'author': 'End to End Technology',
    'sequence': 13,
    'demo': [
        
    ],
    'data': [

        'views/report_payslip_inherit.xml',
        'views/liquidacion_contrato_report.xml',
        'views/hr_payslip_inherit_view.xml',


    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
