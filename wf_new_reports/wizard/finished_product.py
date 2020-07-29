# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, ValidationError ,UserError

class FinishedProductReport(models.TransientModel):
    _name = 'finished.product.report'

    date_from = fields.Date(string="From Date" , required=True)
    date_to  = fields.Date(string="To Date" , required=True)
    category = fields.Many2many('product.category','categ_id','finished_prod_id',string="Finished Product Filter", required=True)
    products = fields.Many2many('product.category','prods_id','pros_cat_id',string="Component Filter")
    show_product = fields.Boolean('Show Components',default=True)

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
        pro2 = []
        for prod in self.products:
            projj = {
                'id':prod.id,
                'name':prod.name,
            }
            pro2.append(projj)
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'from': self.date_from, 'to': self.date_to,'show': self.show_product,'category': pro,'products': pro2,
            },
        }
        return self.env.ref('wf_new_reports.action_report_finished_products').report_action(self, data=data)


    # @api.multi
    # def next_stage_6(self):
    #     pur = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
    #     pur.write({'stage_id': 8})