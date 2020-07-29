# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Employee Self Service',
    'author': 'Ziad',
    'depends': ['mail'],
    'data': [
        'views/ess.xml',
        'security/ir.model.access.csv',
        'security/ESS_security.xml',
        'data/ESS_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
