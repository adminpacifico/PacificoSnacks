{
    'name': "sos_nomina_ss",
    'summary': "Module to manage social security entities in HR contracts",
    'description': """
        This module adds fields for social security entities in HR contracts,
        and integrates them with payroll rules.
    """,
    'author': "Táctica",
    'website': "http://www.tacticaweb.com",
    'category': 'Human Resources',
    'version': '17.0.1.0.0',
    'depends': ['base', 'hr_payroll'],
    'data': [
        'views/views.xml',
    ],
}
