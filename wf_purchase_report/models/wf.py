# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools ,_
from odoo.exceptions import except_orm, ValidationError,UserError
from odoo.exceptions import  AccessError, UserError, RedirectWarning,Warning
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta , date
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import odoo.exceptions
import re 

class PurchaseReportcust(models.Model):
    _inherit = "purchase.report"
   
    name = fields.Many2one('purchase.order', 'Purchase Reference', readonly=True)
    date_planned = fields.Datetime('Scheduled Date', readonly=True)
    purchased_qty = fields.Float('Purchased Qty', readonly=True)
    received_qty = fields.Float('Received Qty', readonly=True)
    billed_qty = fields.Float('Billed Qty', readonly=True)
    

    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
                SELECT
                    min(l.id) as id,
                    s.date_order as date_order,
                    s.state,
                    s.id as name,
                    s.date_approve,
                    l.date_planned as date_planned,
                    l.product_qty as purchased_qty,
                    l.qty_received as received_qty,
                    l.qty_invoiced as billed_qty,
                    s.dest_address_id,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    s.fiscal_position_id as fiscal_position_id,
                    l.product_id,
                    p.product_tmpl_id,
                    t.categ_id as category_id,
                    s.currency_id,
                    t.uom_id as product_uom,
                    sum(l.product_qty/u.factor*u2.factor) as unit_quantity,
                    extract(epoch from age(s.date_approve,s.date_order))/(24*60*60)::decimal(16,2) as delay,
                    extract(epoch from age(l.date_planned,s.date_order))/(24*60*60)::decimal(16,2) as delay_pass,
                    count(*) as nbr_lines,
                    sum(l.price_unit / COALESCE(NULLIF(cr.rate, 0), 1.0) * l.product_qty)::decimal(16,2) as price_total,
                    avg(100.0 * (l.price_unit / COALESCE(NULLIF(cr.rate, 0),1.0) * l.product_qty) / NULLIF(ip.value_float*l.product_qty/u.factor*u2.factor, 0.0))::decimal(16,2) as negociation,
                    sum(ip.value_float*l.product_qty/u.factor*u2.factor)::decimal(16,2) as price_standard,
                    (sum(l.product_qty * l.price_unit / COALESCE(NULLIF(cr.rate, 0), 1.0))/NULLIF(sum(l.product_qty/u.factor*u2.factor),0.0))::decimal(16,2) as price_average,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    analytic_account.id as account_analytic_id,
                    sum(p.weight * l.product_qty/u.factor*u2.factor) as weight,
                    sum(p.volume * l.product_qty/u.factor*u2.factor) as volume
        """ % self.env['res.currency']._select_companies_rates()
        return select_str


    def _group_by(self):
        group_by_str = """
            GROUP BY
                s.company_id,
                s.user_id,
                s.partner_id,
                u.factor,
                s.currency_id,
                l.price_unit,
                s.date_approve,
                l.date_planned,
                l.product_qty,
                l.qty_received,
                l.qty_invoiced,
                l.product_uom,
                s.dest_address_id,
                s.fiscal_position_id,
                l.product_id,
                p.product_tmpl_id,
                t.categ_id,
                s.date_order,
                s.state,
                s.id,
                u.uom_type,
                u.category_id,
                t.uom_id,
                u.id,
                u2.factor,
                partner.country_id,
                partner.commercial_partner_id,
                analytic_account.id
        """
        return group_by_str


# class mrpworkordercust(models.Model):
#     _inherit = "mrp.workorder"

    # tem_lot_id = fields.Many2one('stock.production.lot')

    # def open_tablet_view(self):
    #     self.ensure_one()
    #     if not self.is_user_working and self.working_state != 'blocked':
    #         self.button_start()
    #     lot = 0
    #     if self.active_move_line_ids:
    #         lot = self.active_move_line_ids[0].lot_id.id
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'mrp.workorder',
    #         'views': [[self.env.ref('mfg_wo.mrp_workorder_view_form_tablet').id, 'form']],
    #         'res_id': self.id,
    #         'target': 'fullscreen',
    #         'context': {'default_lot_id':lot },
    #         'flags': {
    #             'headless': True,
    #             'form_view_initial_mode': 'edit',
    #         },
    #     }

    # @api.depends('current_quality_check_id', 'qty_producing')
    # def _compute_component_id(self):
    #     for wo in self.filtered(lambda w: w.state not in ('done', 'cancel')):
    #         if wo.current_quality_check_id.point_id:
    #             wo.component_id = wo.current_quality_check_id.point_id.component_id
    #             wo.test_type = wo.current_quality_check_id.point_id.test_type
    #         elif wo.current_quality_check_id.component_id:
    #             wo.component_id = wo.current_quality_check_id.component_id
    #             wo.test_type = 'register_consumed_materials'
    #         else:
    #             wo.test_type = ''
    #         if wo.test_type == 'register_consumed_materials' and wo.quality_state == 'none':
    #             if wo.current_quality_check_id.component_is_byproduct:
    #                 moves = wo.production_id.move_finished_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.product_id == wo.component_id)
    #             else:
    #                 moves = wo.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.product_id == wo.component_id)
    #             move = moves[:1]
    #             lines = wo.active_move_line_ids.filtered(lambda l: l.move_id in moves)
    #             completed_lines = lines.filtered(lambda l: l.lot_id) if wo.component_tracking != 'none' else lines
    #             wo.component_remaining_qty = float_round(sum(moves.mapped('unit_factor')) * wo.qty_producing - sum(completed_lines.mapped('qty_done')), precision_rounding=move.product_uom.rounding)
    #             wo.component_uom_id = move.product_uom
    #     if self.active_move_line_ids:
    #         for l in self.active_move_line_ids:
    #             if self.component_id.id == l.product_id.id:
    #                 self.lot_id = l.lot_id.id

    # @api.onchange('active_move_line_ids')
    # def bring_lot_id(self):
    #     for rec in self:
    #         # raise UserError(_('test'))
    #         if rec.active_move_line_ids:
    #             x = 0
    #             for l in rec.active_move_line_ids:
    #                 if l.production_id:
    #                     com = self.env['mrp.production'].search([('id','=',l.production_id.id)])
    #                     for res in com:
    #                         for i in res.move_raw_ids:
    #                             if l.product_id.id == i.product_id.id:
    #                                 if i.active_move_line_ids:
    #                                     l.lot_id = i.active_move_line_ids[x].lot_id.id
    #                                     # rec.tem_lot_id = i.active_move_line_ids[x].lot_id.id
    #                                     # self.final_lot_id = i.active_move_line_ids[x].lot_id.id
                                        

    #                 x = x + 1
            # if rec.check_ids:
            #     x = 0
            #     for l in rec.check_ids:
            #         if l.production_id:
            #             com = self.env['mrp.production'].search([('id','=',l.production_id.id)])
            #             for res in com:
            #                 for i in res.move_raw_ids:
            #                     if l.product_id.id == i.product_id.id:
            #                         if i.active_move_line_ids:
            #                             l.lot_id = i.active_move_line_ids[x].lot_id.id
            #         x = x + 1


# class StockMoveLinecust(models.Model):
#     _inherit = 'stock.move.line'

