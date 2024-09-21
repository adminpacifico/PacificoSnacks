# -*- coding: utf-8 -*-
##########################################################################
# Author      : Para ti.co SAS
# Copyright(c): 2024-Present ParA TI.CO SAS
# All Rights Reserved.
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
##########################################################################
{
    'name': 'PT Payroll partners',
    'version': '17.1',
    'category': 'Employees',
    'summary': 'Fields and calculations for pauroll',
    "license":  "Other proprietary",
    'author': 'Para ti.co SAS',
    "website":  "https://www.parati.com.co",
    "description":  "Pt Payroll Partners",
    'depends': ['hr_payroll', 'hr_payroll_account'],
    'data': [
        'views/pt_hr_contract.xml',
        'views/pt_payroll_partner.xml',
    ],
    'installable': True,
    'application': False,
}