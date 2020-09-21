# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
##################################################################################

{
    'name': 'Payslip Payment Register Enterprise',
    'version': '13.0.0.1',
    'summary': 'Customization related to payslip',
    'sequence': 1,
    'author': 'SnepTech',
    'license': 'OPL-1',
    'website': 'https://www.sneptech.com/',
    "price": '49.99',
    "currency": 'USD',
    'description':""" 
        Odoo payslip payment register (Enterprise). This module is aim to register the payslip payments for payrolls.
    """,
    "images":['static/description/Banner.png'],
    'depends':['hr_payroll','account','hr_payroll_account'],
    'data':[
        'views/hr_payslip_view.xml',
        'views/hr_payslip_run_view.xml',
        'views/account_payment_view.xml',
        # 'views/hr_salary_rule_view.xml',
        'views/hr_contract_view.xml',
        'wizard/register_payment_spt.xml',
        'views/hr_payroll_structure.xml',
        ],
        
    'application': True,
    'installable': True,
    'auto_install': False,
}
