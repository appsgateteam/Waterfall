# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Waterfall New Reports',
    'author': 'Ziad Monim',
    'depends': ['wf_updates','sale'],
    'data': [
        'views/wf.xml',
        'report/wf_specification_sheet.xml',
        'report/sale_report.xml',
        'report/production_schedule.xml',
        'report/report_mrp_workorder.xml',
        'report/report_mrp_workorder_without_wo.xml',
        'report/finished_goods.xml',
        'report/qc_inspections.xml',
        'wizard/qc_inspection.xml',
        'wizard/job_costing.xml',
        'wizard/finished_product.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
