# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Waterfall Last Changes',
    'author': 'Ziad Monim',
    'depends': ['mrp'],
    'data': [
        'views/wf.xml',
        'security/mar_security.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
