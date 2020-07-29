# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import itertools
from itertools import groupby
from operator import itemgetter
from dateutil import parser


class Picking(models.Model):
    _inherit = "stock.picking"

    manufacture_picking = fields.Boolean(string="Picking", default=False)
    return_picking = fields.Boolean(string="Return Picking", default=False)

    # @api.multi
    # def action_assign(self):
    #     res = super(Picking, self).action_assign()
    #     self.manufacture_picking = True
    #     return res

    # @api.multi
    def button_raw_validate(self):
        # res = super(Picking, self).button_validate()
        production = self.env['mrp.production'].search([('name', '=', self.origin)], limit=1)
        if production:
            data_lines = []
            return_lines = []
            account_move_obj = self.env['account.move']
            journal_id = self.env['account.journal'].search([('code', '=', 'STJ')])
            sequence = self.name
            narration = self.origin
            for line in self.move_ids_without_package:
                moves = self.mapped('move_lines').filtered(lambda x: x.state == 'confirmed')
                for move in moves:
                    if move:
                        avail_qty = move.product_id.with_context({'location': line.location_id.id}).qty_available
                        if avail_qty == 0:
                            return
                else:
                    credit_account_id = line.product_id.categ_id.property_stock_valuation_account_id.id
                    debit_account_id = line.product_id.categ_id.wip_account_id.id
                    if not debit_account_id:
                        raise UserError('Please set the Wip Account')
                    if line.product_uom_qty > 0:
                        vals2 = {
                            'journal_id': journal_id.id,
                            'name': narration,
                            'product_id': line.product_id.id,
                            'account_id': debit_account_id,
                            'debit': line.product_id.standard_price * line.product_uom_qty,
                            'credit': 0.0,
                        }
                        if vals2['debit'] > 0.0 or vals2['credit'] > 0.0:
                            data_lines.append((0, 0, vals2), )

                        vals1 = {
                            'journal_id': journal_id.id,
                            'name': narration,
                            'product_id': line.product_id.id,
                            'account_id': credit_account_id,
                            'debit': 0.0,
                            'credit': line.product_id.standard_price * line.product_uom_qty,
                        }
                        if vals1['debit'] > 0.0 or vals1['credit'] > 0.0:
                            data_lines.append((0, 0, vals1), )
                        line.write({'price_unit': line.product_id.standard_price})

            if data_lines:
                data = {
                    'journal_id': journal_id.id,
                    'state': 'draft',
                    'ref': sequence,
                    'line_ids': data_lines
                }
                account_move = account_move_obj.create(data)
                account_move.action_post()
        if self.return_picking:
            self.return_picking_production()
        return True

    def return_picking_production(self):
        return_lines = []
        account_move_obj = self.env['account.move']
        journal_id = self.env['account.journal'].search([('code', '=', 'STJ')])
        sequence = self.name
        narration = self.origin
        credit_account_id = self.product_id.categ_id.property_stock_valuation_account_id.id
        debit_account_id = self.product_id.categ_id.wip_account_id.id
        if not debit_account_id:
            raise UserError('Please set the Wip Account')
        for line in self.move_ids_without_package:
            vals4 = {
                'journal_id': journal_id.id,
                'name': narration,
                'product_id': line.product_id.id,
                'account_id': credit_account_id,
                'debit': line.product_id.standard_price,
                'credit': 0.0,
            }
            if vals4['debit'] > 0.0 or vals4['credit'] > 0.0:
                return_lines.append((0, 0, vals4), )

            vals3 = {
                'journal_id': journal_id.id,
                'name': narration,
                'product_id': line.product_id.id,
                'account_id': debit_account_id,
                'debit': 0.0,
                'credit': line.product_id.standard_price,
            }
            if vals3['debit'] > 0.0 or vals3['credit'] > 0.0:
                return_lines.append((0, 0, vals3), )

        if return_lines:
            data = {
                'journal_id': journal_id.id,
                'state': 'draft',
                'ref': sequence,
                'line_ids': return_lines
            }
            account_move = account_move_obj.create(data)
            account_move.action_post()

        return True

    @api.multi
    def unlink(self):
        if self.state == 'assigned':
            raise UserError(_("You can't delete the reserved products."))
        return super(Picking, self).unlink()


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        res = super(StockImmediateTransfer, self).process()
        for picking in self.pick_ids:
            picking.button_raw_validate()
        return res


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        new_picking_id, picking_id = super(ReturnPicking, self)._create_returns()
        production = self.env['mrp.production'].search([('name', '=', self.picking_id.origin)], limit=1)
        if production:
            new_picking = self.env['stock.picking'].browse([new_picking_id])
            for move in new_picking:
                move.return_picking = True
        return new_picking_id, picking_id


class MrpProductionQueries(models.Model):
    _inherit = 'mrp.production'

    update_cost = fields.Boolean(default=False, copy=False)
    compute_cost = fields.Boolean(default=False, copy=False)

    @api.model_cr
    def cancel_workorders(self):
        orders = self.env['mrp.workorder'].search([('production_id', '=', self.id)])
        for order in orders:
            labour = order.labour_move_id.button_cancel()
            overhead = order.overhead_move_id.button_cancel()
        for work_order in self.mapped('workorder_ids'):
            work_order.labour_move_id.unlink()
            work_order.overhead_move_id.unlink()
        self.compute_cost = False
        res = super(MrpProductionQueries, self).cancel_workorders()
        return res

    def button_plan(self):
        res = super(MrpProductionQueries, self).button_plan()
        if self.bom_id:
            workorder = self.env['mrp.workorder'].search([('production_id', '=', self.id)])
            workorder.write({
                'overhead_journal_id': self.bom_id.overhead_journal_id.id,
                'labour_journal_id': self.bom_id.labour_journal_id.id,
            })
        return res

    @api.multi
    def update_product_cost(self):
        product = self.env['product.product'].search([('id', '=', self.product_id.id)])
        product.write({'standard_price': self.unit_cost})
        self.update_cost = True

    @api.multi
    def update_material_cost(self):
        for rec in self:
            # rec.material_total = sum([(p.product_id.standard_price * p.product_qty) for p in rec.bom_id.bom_line_ids])
            rec.total_actual_material_cost = sum([(p.product_id.standard_price * p.quantity_done) if p.price_unit == 0
                                                  else (p.price_unit * p.quantity_done) for p in rec.move_raw_ids])
            product = self.env['product.product'].search([('id', '=', self.product_id.id)])
            product.write({'standard_price': rec.unit_cost})
            rec.compute_cost = True


class StockMove(models.Model):
    _inherit = "stock.move"

    remarks = fields.Text(string="Remarks")
    mrp_product = fields.Boolean(string="Mrp Product")
    raw_product = fields.Boolean(string="Raw Product")

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = super(StockMove, self).onchange_product_id()
        production_id = self.env['mrp.production'].sudo().browse(
            self._context.get('default_raw_material_production_id'))
        # procurement_group_id = production_id.procurement_group_id
        # picking_ids = self.env['stock.picking'].search([
        #     ('group_id', '=', procurement_group_id.id), ('group_id', '!=', False),
        # ])
        product_ids = production_id.picking_ids.mapped('move_ids_without_package').mapped('product_id').ids
        # if product_ids:
        #     result['domain'] = {'product_id': [('id', 'in', product_ids)]}
        pick = self.env['stock.picking'].sudo().browse(self._context.get('default_picking_id'))
        # raise UserError(pick)
        production_ids = self.env['mrp.production'].search([('name','=',pick.origin)])
        if production_ids:
            # production_id = self.env['mrp.production'].sudo().browse(production_ids)
            # raise UserError(production_id)
            # procurement_group_id = production_id.procurement_group_id
            # picking_ids = self.env['stock.picking'].search([
            #     ('group_id', '=', procurement_group_id.id), ('group_id', '!=', False),
            # ])
            product_ids = production_ids.mapped('move_raw_ids').mapped('product_id').ids
            if product_ids:
                result['domain'] = {'product_id': [('id', 'in', product_ids)]}
        return result

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        res = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        for _, _, line in res:
            if self.location_dest_id.scrap_location:
                credit_account_id = self.product_id.categ_id.wip_account_id.id
                debit_account_id = self.location_dest_id.valuation_in_account_id.id
            production = self.env['mrp.production'].search([('name', '=', self.origin), ('id', '=', self.production_id.id)], limit=1)
            if production:
                self.mrp_product = True
            raw_production = self.env['mrp.production'].search(
                [('name', '=', self.origin), ('id', '=', self.raw_material_production_id.id)], limit=1)
            # raise UserError(str(raw_production))
            if raw_production:
                self.raw_product = True
        return res

    def _prepare_finished_journal_entries(self, journal_id):
        account_move_obj = self.env['account.move']
        # journal_id = self.env['account.journal'].search([('code', '=', 'STJ')])
        debit_account_id = self.product_id.categ_id.property_stock_valuation_account_id.id
        production = self.env['mrp.production'].search([('name', '=', self.origin)])
        sequence = production.name
        raw_moves = production.move_raw_ids
        finished_moves = production.move_finished_ids
        datalines = []
        overhead_product_lines = []
        labour_product_lines = []
        for move_1 in raw_moves:
            for product in move_1.product_id:
                credit_account_id = product.categ_id.wip_account_id.id
                vals4 = {
                    'journal_id': journal_id,
                    'name': sequence,
                    'product_id': product.id,
                    'account_id': credit_account_id,
                    'debit': 0.0,
                    'credit': product.standard_price * move_1.quantity_done,
                }
                if vals4['debit'] > 0.0 or vals4['credit'] > 0.0:
                    datalines.append((0, 0, vals4), )
        for move_2 in finished_moves:
            for finished in move_2.product_id:
                vals3 = {
                    'journal_id': journal_id,
                    'name': sequence,
                    'product_id': finished.id,
                    'account_id': debit_account_id,
                    'debit': production.unit_cost,
                    'credit': 0.0,
                }
                if vals3['debit'] > 0.0 or vals3['credit'] > 0.0:
                    datalines.append((0, 0, vals3), )
        for overhead_product in production.mapped('overhead_cost_ids'):
            for overhead in overhead_product.product_id:
                credit_over_id = overhead.property_account_expense_id.id
                vals2 = {
                    'journal_id': journal_id,
                    'name': sequence,
                    'product_id': overhead.id,
                    'account_id': credit_over_id,
                    'debit': 0.0,
                    'credit': overhead_product.total_actual_cost,
                }
                overhead_product_lines.append(vals2)
        data = sorted(overhead_product_lines, key=itemgetter('product_id'))
        for key, value in itertools.groupby(data, key=itemgetter('product_id')):
            cost = 0.0
            for item in list(value):
                cost += float(item['credit'])
            vals_2 = {
                'journal_id': item['journal_id'],
                'name': item['name'],
                'product_id': item['product_id'],
                'account_id': item['account_id'],
                'debit': 0.0,
                'credit': cost,
            }
            if vals_2['debit'] > 0.0 or vals_2['credit'] > 0.0:
                datalines.append((0, 0, vals_2), )
        for labour_product in production.mapped('labour_cost_ids'):
            for labour in labour_product.product_id:
                credit_lab_id = labour.property_account_expense_id.id
                vals1 = {
                    'journal_id': journal_id,
                    'name': sequence,
                    'product_id': labour.id,
                    'account_id': credit_lab_id,
                    'debit': 0.0,
                    'credit': labour_product.total_actual_cost,
                }
                labour_product_lines.append(vals1)
        data = sorted(labour_product_lines, key=itemgetter('product_id'))
        for key, value in itertools.groupby(data, key=itemgetter('product_id')):
            cost = 0.0
            for item in list(value):
                cost += float(item['credit'])
            vals_1 = {
                'journal_id': item['journal_id'],
                'name': item['name'],
                'product_id': item['product_id'],
                'account_id': item['account_id'],
                'debit': 0.0,
                'credit': cost,
            }
            if vals_1['debit'] > 0.0 or vals_1['credit'] > 0.0:
                datalines.append((0, 0, vals_1), )
        if datalines:
            data = {
                'journal_id': journal_id,
                'state': 'draft',
                'ref': sequence,
                'line_ids': datalines
            }
            account_move = account_move_obj.create(data)
            account_move.action_post()
        return True

    def _run_valuation(self, quantity=None):
        res = super(StockMove, self)._run_valuation(quantity)
        for move in self.filtered(lambda m: m.production_id or m.raw_material_production_id):
            if move:
                productions = self.env['mrp.production'].search(
                    [('name', '=', self.origin), ('procurement_group_id', '=', self.group_id.id)])
                for production in productions:
                    for dest_move in move.mapped('move_dest_ids'):
                        dest_move.price_unit = production.unit_cost
                    # dest_move.write({'state': 'done'})
        return res

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
        self.ensure_one()
        AccountMove = self.env['account.move']
        quantity = self.env.context.get('forced_quantity', self.product_qty)
        quantity = quantity if self._is_in() else -1 * quantity

        # Make an informative `ref` on the created account move to differentiate between classic
        # movements, vacuum and edition of past moves.
        ref = self.picking_id.name
        if self.env.context.get('force_valuation_amount'):
            if self.env.context.get('forced_quantity') == 0:
                ref = 'Revaluation of %s (negative inventory)' % ref
            elif self.env.context.get('forced_quantity') is not None:
                ref = 'Correction of %s (modification of past move)' % ref

        move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(self.value),
                                                                                  credit_account_id, debit_account_id)
        if move_lines and self.mrp_product:
            journal_id = journal_id
            self._prepare_finished_journal_entries(journal_id)
        if move_lines and not self.mrp_product and not self.raw_product:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': ref,
                'stock_move_id': self.id,
            })
            # raise UserError(_('You can not consume without telling for which lot you consumed it'))
            new_account_move.post()


class ProductCategory(models.Model):
    _inherit = "product.category"

    wip_account_id = fields.Many2one('account.account', string="WIP Account", domain=[('deprecated', '=', False)])


class MrpProductionWorkcenterLine(models.Model):
    _inherit = 'mrp.workorder'

    def do_finish(self):
        res = super(MrpProductionWorkcenterLine, self).do_finish()
        self.labour_journal()
        self.overhead_journal()
        return res

    def labour_journal(self):
        if self.labour_cost_ids:
            data_lines = []
            account_move_obj = self.env['account.move']
            sequence = self.production_id.name
            labour_journal = self.labour_journal_id.id
            for labour in self.labour_cost_ids:
                if labour.product_id.property_account_income_id:
                    credit_account_id = labour.product_id.property_account_income_id.id
                else:
                    raise UserError("please add the income account for the product %s"% (labour.product_id.name))
                print('credit_account_id', credit_account_id)
                # debit_account_id = labour.product_id.property_account_expense_id.id
                if labour.product_id.property_account_expense_id:
                    debit_account_id = labour.product_id.property_account_expense_id.id
                else:
                    raise UserError("please add the expense account for the product %s"% (labour.product_id.name))
                print('debit_account_id', debit_account_id)
                vals2 = {
                    'journal_id': labour_journal,
                    'name': sequence,
                    'product_id': labour.product_id.id,
                    'account_id': debit_account_id,
                    'debit': labour.total_actual_cost,
                    'credit': 0.0,
                }
                if vals2['debit'] > 0.0 or vals2['credit'] > 0.0:
                    data_lines.append((0, 0, vals2), )

                vals1 = {
                    'journal_id': labour_journal,
                    'name': sequence,
                    'product_id': labour.product_id.id,
                    'account_id': credit_account_id,
                    'debit': 0.0,
                    'credit': labour.total_actual_cost,
                }
                if vals1['debit'] > 0.0 or vals1['credit'] > 0.0:
                    data_lines.append((0, 0, vals1), )
            if data_lines:
                data = {
                    'journal_id': labour_journal,
                    'state': 'draft',
                    'ref': sequence,
                    'line_ids': data_lines
                }
                account_move = account_move_obj.create(data)
                account_move.action_post()
                self.write({'labour_move_id': account_move.id})

    def overhead_journal(self):
        if self.overhead_cost_ids:
            data_lines = []
            account_move_obj = self.env['account.move']
            sequence = self.production_id.name
            overhead_journal = self.overhead_journal_id.id
            for overhead in self.overhead_cost_ids:
                if overhead.product_id.property_account_income_id:
                    credit_account_id = overhead.product_id.property_account_income_id.id
                else:
                    raise UserError("please add the income account for the product %s"% (overhead.product_id.name))
                if overhead.product_id.property_account_expense_id:
                    debit_account_id = overhead.product_id.property_account_expense_id.id
                else:
                    raise UserError("please add the expense account for the product %s"% (overhead.product_id.name))
                # credit_account_id = overhead.product_id.property_account_income_id.id
                # debit_account_id = overhead.product_id.property_account_expense_id.id
                vals3 = {
                    'journal_id': overhead_journal,
                    'name': sequence,
                    'product_id': overhead.product_id.id,
                    'account_id': debit_account_id,
                    'debit': overhead.total_actual_cost,
                    'credit': 0.0,
                }
                if vals3['debit'] > 0.0 or vals3['credit'] > 0.0:
                    data_lines.append((0, 0, vals3), )

                vals4 = {
                    'journal_id': overhead_journal,
                    'name': sequence,
                    'product_id': overhead.product_id.id,
                    'account_id': credit_account_id,
                    'debit': 0.0,
                    'credit': overhead.total_actual_cost,
                }
                if vals4['debit'] > 0.0 or vals4['credit'] > 0.0:
                    data_lines.append((0, 0, vals4), )
            if data_lines:
                data = {
                    'journal_id': overhead_journal,
                    'state': 'draft',
                    'ref': sequence,
                    'line_ids': data_lines
                }
                account_move = account_move_obj.create(data)
                account_move.action_post()
                self.write({'overhead_move_id': account_move.id})


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process(self):
        res = super(StockBackorderConfirmation, self).process()
        for picking in self.pick_ids:
            picking.button_raw_validate()
        return res

# class mrp_bom_inherit(models.Model):
#     _inherit = 'mrp.bom'
#
#     @api.multi
#     def button_approve(self, force=False):
#         res = super(mrp_bom_inherit, self).button_approve(force=False)
#         bom_lines = []
#         self.direct_material_ids.unlink()
#         for line in self.bom_line_ids:
#             vals = {
#                 'product_id': line.product_id.id,
#                 'product_qty': line.product_qty,
#                 'uom_id': line.product_uom_id.id,
#                 'cost_price': line.product_id.standard_price,
#                 'job_type': 'material',
#                 'bom_id': self.id,
#                 'routing_workcenter_id': line.operation_id.id,
#             }
#             print(vals)
#             self.env['bom.job.cost.line'].create(vals)
#         return res
