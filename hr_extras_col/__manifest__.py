# -*- coding: utf-8 -*-

{
    'name': 'HR Extras COL',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Human Resources',
    'website': '',
    'author': '',
    'license': '',
    'application': False,
    'installable': True,
    'depends': [
        'hr',
        'hr_payroll',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',        
        'views/hr_extras_view.xml',
        # 'data/data.xml',
        # 'report/report.xml',
    ],
    'qweb': [
    ]
}
