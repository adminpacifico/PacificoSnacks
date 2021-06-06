# -*- coding: utf-8 -*-

{
    'name': 'Payroll Extended',
    'summary': 'Se extiende funcionalidad para adaptarse a las normativas de nómina de Colombia.',
    'version': '1.2',
    'category': 'Human Resources',
    'website': 'https://www.endtoendt.com/',
    'author': 'End to End Technology by Cesar Quiroga',
    'license': '',
    'application': False,
    'installable': True,
    'depends': [
        'hr',
        'hr_payroll',
        'hr_holidays',
        'analytic',
        'hr_work_entry',
        'hr_payroll_account',
        ],
    'description': '''

========================

''',    
    'data': [
        'views/hr_payslip_input_type_view.xml',
        'views/hr_payroll_view.xml',
        'views/hr_type_payslip_view.xml',
        'views/hr_payslip_run_view.xml',
        'views/hr_rule_parameter_view.xml',
        'views/hr_leave_view.xml',
        'views/hr_contract_vacation_view.xml',
        'views/hr_contract_rtf_view.xml',
        'views/hr_withholding_tax_view.xml',
        'views/hr_deduction_concepts_view.xml',
        'views/hr_deductions_rt_views.xml',
        'views/hr_payroll_data_views.xml',
        'views/hr_payroll_structure_view.xml',
        'views/account_analytic_account_view.xml',
        'views/hr_payroll_payslips_by_employees_views.xml',
        'wizard/generate_hr_work_entry_view.xml',
        'data/data.xml',
        # 'views/hr_contract_view.xml',
        # 'views/report_contributionregistercust.xml',
        # 'report/report.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
    ]
}
