# -*- coding: utf-8 -*-

{
    'name': 'Process Costing in Manufacturing Process',
    'version': '2.2.4',
    'category': 'Manufacturing',
    'summary': """This app allow you to do process costing (Material Cost, Labour Cost, Overheads) for manufacturing orders.""",
    'depends': [
        'mrp',
        'stock',
        'sales_team',
        'stock_account',
        'wf_updates',
        'mrp_workorder_cancel',
    ],
    'description': """
                   """,
    'author': 'Ernst',
    'website': 'http://www.n2n.com',
    'support': 'N2N',
    'images': [],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_inherit_view.xml',
        'views/mrp_bom_view.xml',
        'views/mrp_job_cost_sheet_view.xml',
        'views/mrp_production_view.xml',
        'views/work_order_view.xml',
        'report/manufacturing_report_view.xml',
        'report/bom_report_view.xml',
    ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
