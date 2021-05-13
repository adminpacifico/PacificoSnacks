# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Reportes nomina',
    'version': '1.0',
    'summary': 'summary',
    'description': "reporte generado en epdf nomina empleados",
    'website': 'https://www.endtoendt.com',
    'depends': ['account'],
    'category': 'category',
    'author': 'Enrrique Aguiar',
    'sequence': 13,
    'demo': [
        
    ],
    'data': [

        'views/report_payslip_inherit.xml',
        'views/liquidacion_contrato_report.xml',
        'views/hr_payslip_inherit_view.xml',
        'views/cert_ingresos_retencion.xml',


    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
