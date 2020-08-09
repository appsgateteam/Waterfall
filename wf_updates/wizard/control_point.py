# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, ValidationError ,UserError

class ControlPointCategory(models.TransientModel):
    _name = 'contorl.point.category'

    category = fields.Many2one('product.category',string="Product Category", required=True)
    operations = fields.Many2many('stock.picking.type','stock_type_id','st_type_id',string="Operations", required=True)


    def get_report(self):
        for rec in self:
            values = []
            pick = self.env['quality.point']
            products = self.env['product.template'].search([('categ_id','=',rec.category.id)])
            for x in rec.operations:
                for product in products:
                    if not pick.search([('product_tmpl_id','=',product.id),('picking_type_id','=',x.id)]):
                        vals = {
                            'product_tmpl_id':product.id,
                            'picking_type_id':x.id,
                        }
                        values.append(vals)
            pick.create(values)

        return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }