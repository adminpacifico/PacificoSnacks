# -*- coding: utf-8 -*-

{
    'name': 'Contract Extended',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Human Resources',
    'website': '',
    'author': '',
    'license': '',
    'application': False,
    'installable': True,
    'depends': [
        'hr_contract',
        'hr',
        ],
    'description': '''

========================

''',    
    'data': [
        'views/hr_risk_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_causal_termination_view.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
    ]
}
