# -*- coding: utf-8 -*-
{
    'name': "sc_account_report",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sc_project','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        #'wizard/balance_sheet.xml',
        'wizard/bank_move.xml',
        'report/bank_move_report.xml',
        'wizard/project_payment.xml',
        'report/project_payment_report.xml',

    ],
    
    'application': True
}