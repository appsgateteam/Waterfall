# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools ,_
from odoo.exceptions import except_orm, ValidationError,UserError
from odoo.exceptions import  AccessError, UserError, RedirectWarning,Warning
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta , date
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,float_compare, float_round
import odoo.exceptions
import re 

from dateutil.relativedelta import relativedelta
from odoo.addons import decimal_precision as dp

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


class mrpworkordercust(models.Model):
    _inherit = "mrp.workorder"

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
    
    @api.multi
    def write(self, values):
        #res = super(mrpworkordercust, self).write(values)
        #if list(values.keys()) != ['time_ids'] :
        #    raise UserError(_('You can not change the finished work order.'))
        if values.get('final_lot_id'):
            com = self.env['mrp.workorder'].search([('production_id','=',self.production_id.id),('state','!=',['done','cancel'])])
            for l in com:
                self.env.cr.execute("""update mrp_workorder set final_lot_id = %s where id = %s """ % (values.get('final_lot_id'),l.id))
        return super(mrpworkordercust, self).write(values)


   # @api.onchange('active_move_line_ids')
   # def bring_lot_id(self):
     #   for rec in self:
            # raise UserError(_('test'))
      #      if rec.active_move_line_ids:
        #        x = 0
          ##      for l in rec.active_move_line_ids:
           #         if l.production_id:
            #            com = self.env['mrp.production'].search([('id','=',l.production_id.id)])
            #            for res in com:
           #                 for i in res.move_raw_ids:
            ##                    if l.product_id.id == i.product_id.id:
             #                       if i.active_move_line_ids:
             #                           l.lot_id = i.active_move_line_ids[x].lot_id.id
                                        # rec.tem_lot_id = i.active_move_line_ids[x].lot_id.id
                                        # self.final_lot_id = i.active_move_line_ids[x].lot_id.id
                                        

              #      x = x + 1
                
    @api.onchange('active_move_line_ids')
    def bring_lot_id2(self):
        for rec in self:
            # raise UserError(_('test'))
            if rec.active_move_line_ids:
                x = 0
                for l in rec.active_move_line_ids:
                    if l.production_id:
                        if rec.component_id.id == l.product_id.id:
                            com = self.env['mrp.production'].search([('id','=',l.production_id.id)])
                            for res in com:
                                for i in res.move_raw_ids:
                                    if l.product_id.id == i.product_id.id:
                                        if i.active_move_line_ids:
                                            # raise UserError(_(i.active_move_line_ids[x].lot_id.name))
                                            rec.lot_id = i.active_move_line_ids[x].lot_id.id
                                        # raise UserError(_(rec.lot_id))
                                        # rec.tem_lot_id = i.active_move_line_ids[x].lot_id.id
                                        # self.final_lot_id = i.active_move_line_ids[x].lot_id.id
                                        

                    # x = x + 1

    def _generate_lot_ids(self):
        """ Generate stock move lines """
        self.ensure_one()
        MoveLine = self.env['stock.move.line']
        tracked_moves = self.move_raw_ids.filtered(
            lambda move: move.state not in ('done', 'cancel') and move.product_id.tracking != 'none' and move.product_id != self.production_id.product_id )
        for move in tracked_moves:
            qty = move.unit_factor * self.qty_producing
            if move.product_id.tracking == 'serial':
                while float_compare(qty, 0.0, precision_rounding=move.product_uom.rounding) > 0:
                    MoveLine.create({
                        'move_id': move.id,
                        'product_uom_qty': 0,
                        'product_uom_id': move.product_uom.id,
                        'qty_done': min(1, qty),
                        'production_id': self.production_id.id,
                        'workorder_id': self.id,
                        'product_id': move.product_id.id,
                        'done_wo': False,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                    })
                    qty -= 1
            else:
                MoveLine.create({
                    'move_id': move.id,
                    'product_uom_qty': 0,
                    'product_uom_id': move.product_uom.id,
                    'qty_done': qty,
                    'product_id': move.product_id.id,
                    'production_id': self.production_id.id,
                    'workorder_id': self.id,
                    'done_wo': False,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    })
    
    
    
    @api.multi
    def record_production(self):
        if not self:
            return True

        self.ensure_one()
        if self.qty_producing <= 0:
            raise UserError(_('Please set the quantity you are currently producing. It should be different from zero.'))

        if (self.production_id.product_id.tracking != 'none') and not self.final_lot_id and self.move_raw_ids:
            raise UserError(_('You should provide a lot/serial number for the final product.'))

        # Update quantities done on each raw material line
        # For each untracked component without any 'temporary' move lines,
        # (the new workorder tablet view allows registering consumed quantities for untracked components)
        # we assume that only the theoretical quantity was used
        for move in self.move_raw_ids:
            if move.has_tracking == 'none' and (move.state not in ('done', 'cancel')) \
                        and move.unit_factor and not move.move_line_ids.filtered(lambda ml: not ml.done_wo):
                rounding = move.product_uom.rounding
                if self.product_id.tracking != 'none':
                    qty_to_add = float_round(self.qty_producing * move.unit_factor, precision_rounding=rounding)
                    move._generate_consumed_move_line(qty_to_add, self.final_lot_id)
                elif len(move._get_move_lines()) < 2:
                    move.quantity_done += float_round(self.qty_producing * move.unit_factor, precision_rounding=rounding)
                else:
                    move._set_quantity_done(move.quantity_done + float_round(self.qty_producing * move.unit_factor, precision_rounding=rounding))

        # Transfer quantities from temporary to final move lots or make them final
        for move_line in self.active_move_line_ids:
            # Check if move_line already exists
            if move_line.qty_done <= 0:  # rounding...
                move_line.sudo().unlink()
                continue
            if move_line.product_id.tracking != 'none' and not move_line.lot_id:
                raise UserError(_('You should provide a lot/serial number for a component.'))
            # Search other move_line where it could be added:
            lots = self.move_line_ids.filtered(lambda x: (x.lot_id.id == move_line.lot_id.id) and (not x.lot_produced_id) and (not x.done_move) and (x.product_id == move_line.product_id))
            if lots:
                lots[0].qty_done += move_line.qty_done
                lots[0].lot_produced_id = self.final_lot_id.id
                self._link_to_quality_check(move_line, lots[0])
                move_line.sudo().unlink()
            else:
                move_line.lot_produced_id = self.final_lot_id.id
                move_line.done_wo = True

        self.move_line_ids.filtered(
            lambda move_line: not move_line.done_move and not move_line.lot_produced_id and move_line.qty_done > 0
        ).write({
            'lot_produced_id': self.final_lot_id.id,
            'lot_produced_qty': self.qty_producing
        })

        # If last work order, then post lots used
        # TODO: should be same as checking if for every workorder something has been done?
        if not self.next_work_order_id:
            production_move = self.production_id.move_finished_ids.filtered(
                                lambda x: (x.product_id.id == self.production_id.product_id.id) and (x.state not in ('done', 'cancel')))
            if production_move.product_id.tracking != 'none':
                move_line = production_move.move_line_ids.filtered(lambda x: x.lot_id.id == self.final_lot_id.id)
                if move_line:
                    move_line.product_uom_qty += self.qty_producing
                    move_line.qty_done += self.qty_producing
                else:
                    location_dest_id = production_move.location_dest_id.get_putaway_strategy(self.product_id).id or production_move.location_dest_id.id
                    move_line.create({'move_id': production_move.id,
                             'product_id': production_move.product_id.id,
                             'lot_id': self.final_lot_id.id,
                             'product_uom_qty': self.qty_producing,
                             'product_uom_id': production_move.product_uom.id,
                             'qty_done': self.qty_producing,
                             'workorder_id': self.id,
                             'location_id': production_move.location_id.id,
                             'location_dest_id': location_dest_id,
                    })
            else:
                production_move.quantity_done += self.qty_producing

        if not self.next_work_order_id:
            for by_product_move in self._get_byproduct_move_to_update():
                    if by_product_move.has_tracking != 'serial':
                        values = self._get_byproduct_move_line(by_product_move, self.qty_producing * by_product_move.unit_factor)
                        self.env['stock.move.line'].create(values)
                    elif by_product_move.has_tracking == 'serial':
                        qty_todo = by_product_move.product_uom._compute_quantity(self.qty_producing * by_product_move.unit_factor, by_product_move.product_id.uom_id)
                        for i in range(0, int(float_round(qty_todo, precision_digits=0))):
                            values = self._get_byproduct_move_line(by_product_move, 1)
                            self.env['stock.move.line'].create(values)

        # Update workorder quantity produced
        self.qty_produced += self.qty_producing

        if self.final_lot_id:
            self.final_lot_id.use_next_on_work_order_id = self.next_work_order_id
            self.final_lot_id = False

        # One a piece is produced, you can launch the next work order
        self._start_nextworkorder()

        # Set a qty producing
        rounding = self.production_id.product_uom_id.rounding
        if float_compare(self.qty_produced, self.production_id.product_qty, precision_rounding=rounding) >= 0:
            self.qty_producing = 0
        elif self.production_id.product_id.tracking == 'serial':
            self._assign_default_final_lot_id()
            self.qty_producing = 1.0
            self._generate_lot_ids()
        else:
            self.qty_producing = float_round(self.production_id.product_qty - self.qty_produced, precision_rounding=rounding)
            self._generate_lot_ids()

        if self.next_work_order_id and self.next_work_order_id.state not in ['done', 'cancel'] and self.production_id.product_id.tracking != 'none':
            self.next_work_order_id._assign_default_final_lot_id()

        if float_compare(self.qty_produced, self.production_id.product_qty, precision_rounding=rounding) >= 0:
            self.button_finish()
        return True
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

class MrpProductionQu(models.Model):
    _inherit = 'mrp.production'

    # def button_plan(self):
    #     res = super(MrpProductionQu, self).button_plan()
    #     for x in self.move_raw_ids:
    #         if x.unit_factor == 0:
    #             x.write({'unit_factor':1})
    #     return res

    @api.multi
    def write(self, vals):
        res = super(MrpProductionQu, self).write(vals)
        # if 'date_planned_start' in vals:
        #     moves = (self.mapped('move_raw_ids') + self.mapped('move_finished_ids')).filtered(
        #         lambda r: r.state not in ['done', 'cancel'])
        #     moves.write({
        #         'date_expected': vals['date_planned_start'],
        #     })
        for x in self.move_raw_ids:
            if x.unit_factor == 0:
                x.write({'unit_factor':1})
        return res

# class StockMoveLinecust(models.Model):
#     _inherit = 'stock.move.line'

