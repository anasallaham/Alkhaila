# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payroll Edition',
    'version': '13.0.2.0.1',
    'category': 'Accounting',
    'summary': 'Edit Payroll ',
    'live_test_url': '',
    'sequence': '1',
    'website': '',
    'author': 'Abdelraheem',
    'maintainer': 'Odoo Mates',
    'license': 'LGPL-3',
    'support': 'prog.abdelraheem@gmail.com',
    'website': '',
    'depends': ['hr_payroll','account','account_asset'],
    'demo': [],
    'data': [
        'views/hr_payslip.xml',
        'views/hr_contract.xml',
        'views/hr_employee.xml',
        'views/hr_salary_rule.xml',
        'views/advanced_salary.xml',

        'views/sequance.xml',
        'views/iqama_renew_sequence.xml',
        'views/iqama_renew_view.xml',
        'views/exit_entry.xml',
        'views/hr_employee_view.xml',

        'security/ir.model.access.csv'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': [''],
    'qweb': [],
}
