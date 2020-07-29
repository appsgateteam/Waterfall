# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, ValidationError ,UserError

class prodscheduleReport(models.TransientModel):
    _name = 'prod.schedule.report'

    date_from = fields.Date(string="From Date" , required=True)
    date_to  = fields.Date(string="To Date" , required=True)
    category = fields.Many2many('product.category','category_id','prod_schedule_id',string="Product Category", required=True)

    @api.constrains('date_from','date_to')
    def check_inv_date(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                if rec.date_to <=  rec.date_from :
                    raise ValidationError(_("To date should be greater than the from date"))

    
    def get_report(self):
        pro = []
        for l in self.category:
            proj = {
                'id':l.id,
                'name':l.name,
            }
            pro.append(proj)
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'from': self.date_from, 'to': self.date_to,'category': pro,
            },
        }
        return self.env.ref('wf_new_reports.action_report_production_schedule').report_action(self, data=data)


    # @api.multi
    # def next_stage_6(self):
    #     pur = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
    #     pur.write({'stage_id': 8})