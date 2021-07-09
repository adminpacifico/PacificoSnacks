# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Libro de vacaciones',
    'version': '1.0',
    'summary': 'reporte en excel relacion, de vacaciones por empleado, estructura o general',
    'description': "reportes Nomina",
    'website': 'https://www.endtoendt.com',
    'depends': ['account'],
    'category': 'Human Resources',
    'author': 'End to End Technology',
    'sequence': 13,
    'demo': [
        
    ],
    'description': 'reporte en excel relacion, de vacaciones por empleado, estructura o general',
    'data': [

        'views/vacations_report_view.xml',

    ],
    'qweb': [

    ],
    'installable': True,
    'auto_install': False,

}
