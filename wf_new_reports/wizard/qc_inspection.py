# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, ValidationError ,UserError

class QcInspectionReport(models.TransientModel):
    _name = 'qc.inspection.report'

    picking = fields.Many2one('stock.picking',string="Store Ref.")
    production = fields.Many2one('mrp.production',string="Manufacturing Ref.")

    def get_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'picking': self.picking.id,
                'production': self.production.id,
                'production_name': self.production.name,
                'picking_name': self.picking.name,
            },
        }
        return self.env.ref('wf_new_reports.action_qc_inspection_report').report_action(self, data=data)


    # @api.multi
    # def next_stage_6(self):
    #     pur = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
    #     pur.write({'stage_id': 8})