from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta , date
# from datetime import datetime,date
from num2words import num2words
from odoo.tools import float_utils, float_compare
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

# ?????????????????????????????????????????????????????????????????????????????
# quality_alert_NCR_report


class quality_alert_report_detals(models.Model):
    _inherit = "quality.alert"

    name_seq = fields.Char('Name',copy=False, default='New')
    report_n = fields.Char('Report No')
    dtoday = fields.Date('Date' , compute="_com_today")
    reported_by  = fields.Char('Reported by')
    designation = fields.Char('Designation')
    discovered_at = fields.Char('Discovered at')
    type_of_non_con = fields.Char('Type of Non-Conformance')
    qty_affected = fields.Char('Qty.Affected')
    p_o_no = fields.Char('Reference Doc')
    other = fields.Char('Other(s)')
    prepared_by = fields.Many2one('res.users','Prepared by:') 
    reviewed_by = fields.Many2one('res.users','Reviewed by:')
    approved_by = fields.Many2one('res.users','Approved By')
    closed_by = fields.Many2one('res.users','Closed By')
    use_as_is  = fields.Boolean('USE AS IS ',default=False)
    re_work  = fields.Boolean('RE-WORK / REPAIR ',default=False) 
    replac  = fields.Boolean('REPLACEMENT',default=False) 
    scrap  = fields.Boolean('SCRAP ',default=False) 
    return_to_provider  = fields.Boolean('RETURN TO PROVIDER',default=False) 
    other_specify  = fields.Boolean('OTHERS (Specify) ',default=False)
    remarks = fields.Text('Remarks:')
    verification = fields.Text('Verification of Disposition:') 
    approv_date = fields.Date('Date')
    close_date = fields.Date('Date')

    _sql_constraints = [
        ('name_seq_uniq', 'unique(name_seq)', "The sequence should be uniqe !"),
    ]

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('quality.alert') or _('New')
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('quality.alerts.sequence') or 'New'    

        return super(quality_alert_report_detals, self).create(vals) 



    @api.multi
    def write(self, vals):
        if vals.get('stage_id') == 4:
            vals['approv_date'] =  date.today()

        return super(quality_alert_report_detals, self).write(vals)

        


    @api.onchange('closed_by')
    def _app_date(self):
        for rec in self :
            if rec.closed_by:
                rec.close_date =  date.today()
            else:
                rec.close_date = False


    

    @api.multi
    def _com_today(self):
        for rec in self:
            rec.dtoday =  date.today()





class quality_inherit(models.Model):
    _inherit = "quality.point"

    quality_attach = fields.Binary("Upload Quality Attachment", attachment=True,help="This field for Upload Attachment for Quality Check")

class quality_check_inherit(models.Model):
    _inherit = "quality.check"

    quality_att = fields.Binary(String="Quality Attachment", attachment=True,compute="_compute_attach",help="This field for Upload Attachment for Quality Check")
    quality_attac = fields.Binary("Upload Quality Attachment", attachment=True,help="This field for Upload Attachment for Quality Check")
    quality_state = fields.Selection([
        ('none', 'To do'),
        ('pass', 'Passed'),
        ('fail', 'Failed'),('close', 'closed')], string='Status', track_visibility='onchange',
        default='none', copy=False)
    notes = fields.Text('Note')
    source_origin = fields.Char('Source',related='picking_id.origin',readonly=True,store=True)
    source_origin_mo = fields.Many2one('mrp.production',string='Source MO',related='workorder_id.production_id',readonly=True,store=True)
    lot_name = fields.Text('Lot Number',compute='_get_lot')

    @api.depends('picking_id')
    def _get_lot(self):
        for rec in self:
            lot = ''
            coms = self.env['stock.picking'].search([('id','=',rec.picking_id.id)])
            for x in coms:
                for pro in x.move_ids_without_package:
                    if rec.product_id.id == pro.product_id.id:
                        for line in pro.move_line_ids:
                            if line.lot_id:
                                if lot == '':
                                    lot = line.lot_id.name
                                else:
                                    lot = line.lot_id.name + '\n' + lot
                        break
            rec.lot_name = lot

    @api.depends('point_id')
    def _compute_attach(self):
        periods = self.env['quality.point'].search([('id','=',self.point_id.id)])
        self.quality_att = periods.quality_attach

    def do_close(self):
        self.write({'quality_state': 'close',
                    'user_id': self.env.user.id,
                    'control_date': date.today()})
        return self.redirect_after_pass_fail()


class hr_employee_inherit(models.Model):
    _inherit = "hr.employee"

    user_ref = fields.Char('User ID Internal')

    _sql_constraints = [
        ('user_ref_uniq', 'unique(user_ref)', "A User ID Internal must be unique !"),
    ]



class stock_picking_inherit(models.Model):
    _inherit = "stock.picking"

    order = fields.Char('MO Actual State',readonly="1",compute="_com_mo")
    hide = fields.Boolean(string='Hide', compute="_compute_hide")
    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$4new enhancement
    package_line_ids = fields.One2many('package.line','package_id',string='Package Lines')
    # package_line_id = fields.One2many('package.line.inh','package_id',string='Package sub Lines')
    po_number = fields.Char('Purchase Order#')
    comm = fields.Char('Commercial Invoice')
    hs_code = fields.Char('HS Code')
    mode_tran = fields.Char('Mode of Transport')
    product_line_ids = fields.One2many('product.line','product_id',string='product Lines',compute="_return_product_data")
    product_line_idss = fields.One2many('product2.line','product_id',string='product Lines',compute="_return_product_data")
    package_number = fields.Float('Package Number',compute="_sumation")
    total_gross = fields.Float('Package Number',compute="_sumation")
    total_net = fields.Float('Package Number',compute="_sumation")
    total_qty = fields.Float('Package Number',compute="_sumation")
    packing_list = fields.Boolean('Packing List',default=False)
    total_price = fields.Float('Total Price',compute="_total_price")
    dtoday = fields.Date('current Date' , compute="_com_today")


    # Fouad add product fields for pivot 
    # product_id = fields.Many2one('product.product', string='pro', store=True , compute="_get_data")
    # product = fields.Char(string ="product.product" ,  store=True , compute="_get_data")

    product_id = fields.Many2one('product.product', string='product category', store=True , compute="_get_data")
    product = fields.Char(related='product_id.name', store=True)
    detail_data = fields.Char('Order Details',compute='_get_items')

    @api.multi
    def _get_items(self):
        for rec in self:
            if rec.origin:
                production_ids = self.env['mrp.production'].search([('name','=',rec.origin)])
                for l in production_ids:
                    # self.so_ref = y.
                    sale_order = self.env['sale.order'].search([('name','=',l.origin)])
                    for y in sale_order:
                        # self.so_ref = y.name
                        for x in y.order_line:
                            rec.detail_data = """%s , %s , [%s]%s """ % (y.name,y.partner_id.name,x.product_id.product_tmpl_id.default_code,x.product_id.product_tmpl_id.name)

    @api.multi
    def write(self, vals):
        res = super(stock_picking_inherit, self).write(vals)
        for recs in self:
        # Change locations of moves if those of the picking change
            after_vals = {}
            if vals.get('location_id'):
                after_vals['location_id'] = vals['location_id']
            if vals.get('location_dest_id'):
                after_vals['location_dest_id'] = vals['location_dest_id']
            if after_vals:
                self.mapped('move_lines').filtered(lambda move: not move.scrapped).write(after_vals)
            if vals.get('move_lines'):
                # Do not run autoconfirm if any of the moves has an initial demand. If an initial demand
                # is present in any of the moves, it means the picking was created through the "planned
                # transfer" mechanism.
                pickings_to_not_autoconfirm = self.env['stock.picking']
                for picking in self:
                    if picking.state != 'draft':
                        continue
                    for move in picking.move_lines:
                        if not float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                            pickings_to_not_autoconfirm |= picking
                            break
                (self - pickings_to_not_autoconfirm)._autoconfirm_picking()
            if recs.move_ids_without_package :
                for rec in recs.move_ids_without_package:
                    if rec.quantity_done != rec.product_uom_qty:
                        if rec.product_uom_qty == 0:
                            continue
                        elif rec.product_uom_qty == rec.reserved_availability and rec.product_uom_qty !=0 :
                            continue
                        elif rec.product_uom_qty > rec.reserved_availability and rec.reserved_availability !=0:
                            rec.write({'state':'partially_available'})
                        elif rec.product_uom_qty > rec.reserved_availability and rec.reserved_availability == 0:
                            rec.write({'state':'confirmed'})
        

        return res

    
    @api.multi
    def _get_data(self):
        for rec in self:
            invoice_line_pool = rec.pool.get("stock.picking")
            invoice_lines = invoice_line_pool.read(rec.move_ids_without_package , ["product_id"])
            for l in  invoice_lines :
            # record = self.env['stock.picking'].search([('id', '=', rec.origin)])
                product_list = []
                # for lin in record_collection:
                product_list.append(l.product_id.name)
                # rec.product = product_list[:-1] 

        return product_list

                    # record_collection = self.env['product.product'].search([('id', '=', l.product_id.id)])
                    



        #           for record in self:
        
        # for line in record.weather_ids:
        #     temperature_list.append(line.temperature)
        # self.temperature = record.temperature_list[-1]      









    # @api.multi
    # def _get_data(self):
    #     for rec in self:
    #         for l in rec.move_ids_without_package :
    #             result = []
    #             i = 0
    #             record_collection = self.env['product.product'].search([('id', '=', l.product_id.id)])
    #             for lin in record_collection:
    #                  vaul = {
    #                     'product': lin.name
                       
    #                     }
    #                  result.append(vaul)
    #                  rec.product_id = result[i]
    #                  i + 1 

    #                 # rec.product_id = lin.id

    #             return result




    @api.multi
    def _com_today(self):
        for rec in self:
            rec.dtoday = date.today()
    

    @api.depends('name')
    def _name_sale(self):
        # self.package_ids.package_id = self.name
        self.product_line_ids.product_id = self.name

    @api.depends('product_line_ids')
    def _total_price(self):
        for rec in self:
            i = 0.0
            for line in rec.move_ids_without_package:
                i = i + line.price_unit
            rec.total_price = abs(i)

    @api.depends('package_line_ids')
    def _sumation(self):
        for rec in self:
            i = 0
            gro = 0.0
            net = 0
            qty = 0
            for line in rec.package_line_ids:
                i = i+1
                gro = gro + line.package_gross
                for l in line.Package_detail:
                    net = net + l.package_net
                    qty = qty + l.package_qty
            rec.total_gross = gro
            rec.package_number = i
            
            rec.total_net = net
            rec.total_qty = qty

    @api.multi
    @api.depends('name')
    def _return_product_data(self):
        vals = {}
        invoice_line = []
        invoice_line2 = []
        i = 0
        for rec in self:
            for l in rec.move_ids_without_package:
                # raise UserError(_(line.product_id.default_code))
                # pro = self.env['mrp.production'].search([('product_id','=',line.product_id.default_code),('origin','=',line.origin)])
                # for x in pro:
                    # for l in x.move_raw_ids:
                        # raise UserError(_(test)) ,('routing_id','=','Assembly for Electric Motor Driven Pump Unit')
                if self.env['mrp.bom'].search([('product_tmpl_id','=',l.product_id.default_code)]):
                    if l.move_line_ids:
                        for n in l.move_line_ids:
                            if l.quantity_done == 0:
                                # raise UserError(_('electric'))
                                pro_dic = {'product_id':rec.id,'product':l.product_id.name,'qty':l.product_uom_qty,'types':l.product_id.default_code,'status':'','no':n.lot_id.name,'bom':1,'price':abs(l.price_unit)}
                            else :
                                pro_dic = {'product_id':rec.id,'product':l.product_id.name,'qty':l.product_uom_qty,'types':l.product_id.default_code,'status':'','no':n.lot_id.name,'bom':1,'price':abs(l.price_unit)}
                            invoice_line.append((0,0,pro_dic))
                    else:
                        if l.quantity_done == 0:
                            # raise UserError(_('electric'))
                            pro_dic = {'product_id':rec.id,'product':l.product_id.name,'qty':l.product_uom_qty,'types':l.product_id.default_code,'status':'','no':'','bom':1,'price':abs(l.price_unit)}
                        else :
                            pro_dic = {'product_id':rec.id,'product':l.product_id.name,'qty':l.product_uom_qty,'types':l.product_id.default_code,'status':'','no':'','bom':1,'price':abs(l.price_unit)}
                        invoice_line.append((0,0,pro_dic))
                    pro = self.env['mrp.production'].search([('product_id','=',l.product_id.default_code),('origin','=',rec.origin)])
                    if pro:
                        # raise UserError(_(pro))
                        for x in pro:
                            for y in x.move_raw_ids:
                                if y.active_move_line_ids:
                                    for n in y.active_move_line_ids:
                                        if y.quantity_done == 0:
                                            # raise UserError(_('electric'))
                                            pro_dic2 = {'product_id':rec.id,'product':y.product_id.name,'qty':y.product_uom_qty,'types':l.product_id.default_code,'status':'','no':n.lot_id.name,'bom':1,'price':abs(y.price_unit)}
                                        else :
                                            pro_dic2 = {'product_id':rec.id,'product':y.product_id.name,'qty':y.product_uom_qty,'types':l.product_id.default_code,'status':'','no':n.lot_id.name,'bom':1,'price':abs(y.price_unit)}
                                        invoice_line2.append((0,0,pro_dic2))
                                else:
                                    if y.quantity_done == 0:
                                        # raise UserError(_('electric'))
                                        pro_dic2 = {'product_id':rec.id,'product':y.product_id.name,'qty':y.product_uom_qty,'types':l.product_id.default_code,'status':'','no':'','bom':1,'price':abs(y.price_unit)}
                                    else :
                                        pro_dic2 = {'product_id':rec.id,'product':y.product_id.name,'qty':y.product_uom_qty,'types':l.product_id.default_code,'status':'','no':'','bom':1,'price':abs(y.price_unit)}
                                    invoice_line2.append((0,0,pro_dic2))
                            # raise UserError(_(pro_dic2))

                # elif self.env['mrp.bom'].search([('product_tmpl_id','=',l.product_id.default_code),('routing_id','=','Assembly for Diesel Engine Driven Pump Unit')]):
                #     if l.quantity_done == 0:
                #         # raise UserError(_('diesel'))
                #         pro_dic = {'product_id':rec.id,'product':l.product_id.name,'qty':l.product_uom_qty,'types':'diesel','status':'NG','no':'123',}
                #     else : 
                #         pro_dic = {'product_id':rec.id,'product':l.product_id.name,'qty':l.product_uom_qty,'types':'diesel','status':'G','no':'123',}
                else:
                    if l.move_line_ids:
                        for n in l.move_line_ids:
                            if l.quantity_done == 0:
                                #raise UserError(_('acc'))
                                pro_dic = {'product_id':rec.id,'product':l.product_id.name,'qty':l.product_uom_qty,'types':'acc','status':'','no':n.lot_id.name,'bom':0,'price':abs(l.price_unit)}
                                
                            else :
                                pro_dic = {'product_id':rec.id,'product':l.product_id.name,'qty':l.product_uom_qty,'types':'acc','status':'','no':n.lot_id.name,'bom':0,'price':abs(l.price_unit)}
                            invoice_line.append((0,0,pro_dic))
                    else:
                        if l.quantity_done == 0:
                            #raise UserError(_('acc'))
                            pro_dic = {'product_id':rec.id,'product':l.product_id.name,'qty':l.product_uom_qty,'types':'acc','status':'','no':'','bom':0,'price':abs(l.price_unit)}
                            
                        else :
                            pro_dic = {'product_id':rec.id,'product':l.product_id.name,'qty':l.product_uom_qty,'types':'acc','status':'','no':'','bom':0,'price':abs(l.price_unit)}
                        invoice_line.append((0,0,pro_dic))
                i = i + 1
    # pro_dic = {'pro_id':self.name,'product':self.name}
    # pro_dic= {'pro_id':rec.name,'product':rec.name,'qty':rec.name,'type':'electric','status':'G','no':'123',}
                # invoice_line.append((0,0,pro_dic))
                        # self.env['stock.picking'].write({
                        #     'product_line_ids': invoice_line,
                        #     })      
        vals = ({'product_line_ids': invoice_line,'product_line_idss': invoice_line2})
        # raise UserError(_(vals))
        super(stock_picking_inherit, self).update(vals)
        # return{'product_line_ids': invoice_line,}
        # raise UserError(_(vals))

        
        # super(stock_picking_inherit, self).update(vals)

    
    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$4new enhancement

    @api.multi
    def action_draft(self):
        return self.write({'state': 'waiting'})

    @api.depends('partner_id')
    def _compute_hide(self):
        if self.partner_id.customer == True:
            self.hide = True
        else:
            self.hide = False

    @api.multi
    @api.depends('origin')
    def _com_mo(self):
        for rec in self:
            mo = self.env['mrp.production'].search([('origin','=',rec.origin)])
            for n in mo:
                rec.order = n.state
            
   

# Product data part

# class sale_wf_inherit(models.Model):
#     _inherit = "sale.order"

#     dtoday = fields.Date('current Date' , default=date.today())
class mrp_bom_inherit(models.Model):
    _inherit = "mrp.bom"

    the_code = fields.Char(
    related='product_tmpl_id.default_code',
    readonly=True,
    store=True
    )
    bom_nam = fields.Char('BOM Name appears in Quotation')
    # BOM Approve
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve','To Approve'),
        ('done', 'Approved')], string='Status', default='draft', index=True)

    @api.onchange('product_tmpl_id')
    def _const_name(self):
        for l in self:
            com = self.env['mrp.bom'].search([('product_tmpl_id','=',l.product_tmpl_id.default_code)])
            if com:
                raise ValidationError(_('this Product already use in BOM and it must be unique!'))
            else:
                continue

    @api.multi
    def action_validate(self):
        return self.write({'state': 'approve'})

    @api.multi
    def action_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def button_approve(self, force=False):
        return self.write({'state': 'done'})


class sale_wf_inherit(models.Model):
    _inherit = "sale.order"


    sale_order_option_ids = fields.One2many(
        'sale.order.option', 'order_id', 'Optional Products Lines', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},copy=False,compute="_com_items")
    # sale_order_options_ids = fields.One2many(
    #     'sale.order.option', 'order_id', 'Optional Products Lines',
    #     copy=True, readonly=True,
    #     states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},compute="_com_sub_items")
    text = fields.Char('Price in Text',compute="_com_price2",invisible=True)
    version = fields.Char('Version Number')
    version_date = fields.Date('Version Date',default=date.today())
    dtoday = fields.Date('current Date' , compute="_com_today")
    contact_person = fields.Char('Contact Person Name')
    project_name = fields.Char('Project Name')
    project_loc = fields.Char('Project Location')
    pro_nam = fields.Char('Product Name appear in Quotation')
    cus_date = fields.Date('Ref Date')
    sign_sale = fields.Char('Salesman Signature',compute="_sales_sign")
    sign_man = fields.Many2one('res.users','Manager Signature')
    old = fields.Char('Old Reference')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('approve', 'To Approve'),
        ('approved', 'Approved'),
        ('final', 'In Final Approve'),
        ('finalapp', 'Final Approved Done'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
    # current_user = fields.Many2one('res.users','Current User', default=lambda self: self.env.user)
    test = fields.Boolean('Test',compute='_com_user')
    country = fields.Many2one('res.country', string='Country of Destination')
    # additional fields for the enhacement in note details
    scope = fields.Text('Scope of work detail')
    terms = fields.Text('Terms detail')
    notess = fields.Text('Notes detail')
    exclue = fields.Text('EXCLUSIONS detail')
    entire = fields.Char('Price in Text',compute="_com_price")
    decimal = fields.Char('Price in Text',compute="_com_price")
    curr_change_untaxed = fields.Float('Untaxed Amount in AED',compute='_amount_change')
    curr_change_total = fields.Float('Total Amount in AED',compute='_amount_change')

    # test start fouad

    bal_amount = fields.Float('Amount in AED',compute='_get_fields_data')
    paid_amount = fields.Float('Paid Amount in AED',compute='_get_fields_data')
    inv_date = fields.Date('current Date' , compute="_get_fields_data")

    # new changes ziad
    submittal_ref = fields.Char('Submittal Reference')
    pump_capacity = fields.Char('Pump Capacity')
    pressure_bar = fields.Char('Pressure (Bar)')
    listing = fields.Char('Listing')
    ttype = fields.Char('Type')
    sp_remark = fields.Text('General Remarks')
    specification_date = fields.Date('Specification Date')
    commitment_date = fields.Datetime('Commitment Date',
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        copy=False, oldname='requested_date', readonly=False,
        help="This is the delivery date promised to the customer. If set, the delivery order "
             "will be scheduled based on this date rather than product lead times.")
    # new changes ziad

    receive_state = fields.Selection(string='Current State', selection=[
        ('New','New'),
        ('Ready','Ready'),
        ('Partially Available','Partially Available'),
        ('Partially Delivery','Partially Delivery'),
        ('Delivered','Delivered')],
        copy=False, index=True, readonly=True,compute="ready_state")


    # @api.model
    # def _cancel_auto_rfqqq(self):
    #     com = self.env['purchase.order'].search([('user_id','=',1),('state','!=','cancel')])
    #     for rec in com:
    #         rec.write({'state':'cancel'})

    @api.multi
    @api.depends('expected_date')
    def ready_state(self):
        current_date = date.today()
        for rec in self:
        # raise UserError(_(self.date_planned.date()))
            if (rec.state == 'draft','sent','approve','approved','final','finalapp') and (rec.date_order.date() > current_date):
                rec.receive_state = 'New'
            if (rec.expected_date and rec.expected_date.date() <= current_date):
                rec.receive_state = 'Ready'
            if rec.state == 'sale':
                # rec.receive_state = 'part'
                com = self.env['stock.picking'].search([('origin','=',rec.name)])
                if len(com) == 1:
                    for line in com:
                        if line.state == 'done':
                            rec.receive_state = 'Delivered'
                        else:
                            y = 0
                            x = 0
                            z = len(line.move_ids_without_package)
                            for l in line.move_ids_without_package:
                                if l.reserved_availability == 0.0 and l.quantity_done == 0.0:
                                    if (rec.expected_date and rec.expected_date.date() <= current_date):
                                        rec.receive_state = 'Ready'
                                    else:
                                        rec.receive_state = 'New'
                                    
                                else:
                                    rec.receive_state = 'Partially Available'
                                #     if l.product_uom_qty == l.reserverd_availability:
                                #         y = y + 1
                                #         continue
                                #     else:
                                #         x = x + 1
                                # else:
                            # if z == x:
                            #     if (rec.expected_date and rec.expected_date.date() <= current_date):
                            #         rec.receive_state = 'Ready'
                            #     else:
                            #         rec.receive_state = 'New'
                            # else:
                            #     rec.receive_state = 'Partially Available'
                else:
                    for line in com:
                        if line.state != 'done':
                            rec.receive_state = 'Partially Delivery'
                            break
                        else:
                            rec.receive_state = 'Delivered'



    @api.multi
    def _get_fields_data(self):
        for rec in self:
            x = 0.0
            y = 0.0
            com = self.env['account.invoice'].search([('origin','=',rec.name)])
            for l in com:
                x = x + l.amount_total
                if l.residual == 0.0 or l.residual <= l.amount_tax:
                    y = y + l.residual
                else:
                    y = y + (l.residual - l.amount_tax)
                rec.inv_date = l.date_invoice
                rec.paid_amount = x - y
                rec.bal_amount = y 

    # test end fouad 

    @api.multi
    def _amount_change(self):
        for rec in self:
            currency = rec.pricelist_id.currency_id
            rec.curr_change_total = currency._convert(rec.amount_total, self.env.user.company_id.currency_id, self.env.user.company_id, rec.date_order or date.today())
            rec.curr_change_untaxed = currency._convert(rec.amount_untaxed, self.env.user.company_id.currency_id, self.env.user.company_id, rec.date_order or date.today())
            

    @api.depends('amount_total','pricelist_id')
    def _com_price2(self):
        # res = super(pur_order_inherit, self)._onchange_amount()
        self.text = self.pricelist_id.currency_id.amount_to_text(self.amount_total) if self.currency_id else ''
        self.text = self.text.replace(' And ', ' ')

    @api.multi
    def _com_price(self):
        # self.text = num2words(self.amount_total, lang='en')
        pre = float(self.amount_total)
        text1 = ''
        entire_num = int((str(pre).split('.'))[0])
        decimal_num = int((str(pre).split('.'))[1])
        if decimal_num < 10:
            decimal_num = decimal_num * 10        
        text1+=num2words(entire_num, lang='en')
        self.entire = num2words(entire_num, lang='en')
        self.entire = self.entire.replace(' and ', ' ')
        text1+=' and '
        text1+=num2words(decimal_num, lang='en')
        self.decimal = num2words(decimal_num, lang='en')
        #self.text = text1
    # additional fields for the enhacement in note details

    @api.multi
    def _com_today(self):
        for rec in self:
            rec.dtoday = date.today()

    @api.multi
    def _com_user(self):
        for rec in self:
            if rec.user_id.id == rec.env.uid :
                rec.test = True
            else:
                rec.test = False


    @api.depends('user_id')
    def _sales_sign(self):
        for rec in self:
            rec.sign_sale = rec.user_id.name

    @api.multi
    def action_to_approve(self):
        return self.write({'state': 'approve'})

    @api.multi
    def send_to_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def action_approve(self):
        return self.write({'state': 'approved'})

    @api.multi
    def action_to_final(self):
        return self.write({'state': 'final'})

    @api.multi
    def action_to_finalapp(self):
        return self.write({'state': 'finalapp'})

    # @api.multi
    # def action_confirm(self):
    #     if self._get_forbidden_state_confirm() & set(self.mapped('state')):
    #         raise UserError(_(
    #             'It is not allowed to confirm an order in the following states: %s'
    #         ) % (', '.join(self._get_forbidden_state_confirm())))

    #     for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
    #         order.message_subscribe([order.partner_id.id])
    #     self.write({
    #         'state': 'sale',
    #         'confirmation_date': fields.Datetime.now()
    #     })
    #     self._action_confirm()
    #     if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
    #         self.action_done()
    #     self._cancel_auto_rfqqq()
    #     return True

    # @api.multi
    # def button_approve(self, force=False):
    #     if self._get_forbidden_state_confirm() & set(self.mapped('state')):
    #         raise UserError(_(
    #             'It is not allowed to confirm an order in the following states: %s'
    #         ) % (', '.join(self._get_forbidden_state_confirm())))

    #     for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
    #         order.message_subscribe([order.partner_id.id])
    #     self.write({
    #         'state': 'sale',
    #         'confirmation_date': fields.Datetime.now(),
    #         'approve_date': fields.Date.context_today(self)
    #     })
    #     self._action_confirm()
    #     if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
    #         self.action_done()
    #     return True

    # @api.onchange('amount_total','pricelist_id')
    # def _onchange_amount(self):
    #     res = super(sale_wf_inherit, self)._onchange_amount()
    #     self.text = self.pricelist_id.currency_id.amount_to_text(self.amount_total) if self.pricelist_id.currency_id else ''
    #     return res

    @api.multi
    @api.depends('order_line')
    def _com_items(self):
        vals = {}
        invoice_line = []
        for rec in self:
            for l in rec.order_line:
                com = self.env['mrp.bom'].search([('product_tmpl_id','=',l.product_id.code)])
                # com = com.read([])
                if not com:
                    break
                for n in com.bom_line_ids:
                    coz = self.env['mrp.bom'].search([('product_tmpl_id','=',n.product_id.code)])
                    if len(coz) <= 1:
                        invoice_line_vals = {'product_id': n.product_id,
                                            'name':n.product_id.name,
                                            'uom_id':n.product_uom_id,
                                            'quantity':n.product_qty * l.product_uom_qty,
                                            'bom_nam':coz.bom_nam,
                                            'check': 1,
                                            'flow': n.product_id.flow,
                                            'flow_uom_id': n.product_id.flow_uom_id,
                                            'head': n.product_id.head,
                                            'Type': n.product_id.Type,
                                            'Type_dr': n.product_id.Type_dr,
                                            'Type_con': n.product_id.Type_con,
                                            'manu': n.product_id.manu,
                                            'manu_dr': n.product_id.manu_dr,
                                            'manu_con': n.product_id.manu_con,
                                            'model': n.product_id.model,
                                            'model_dr': n.product_id.model_dr,
                                            'listing': n.product_id.listing,
                                            'listing_dr': n.product_id.listing_dr,
                                            'listing_con': n.product_id.listing_con,
                                            'con': n.product_id.con,
                                            'supply_dr': n.product_id.supply_dr,
                                            'supply_con': n.product_id.supply_con,
                                            'enc_dr': n.product_id.enc_dr,
                                            'enc_con': n.product_id.enc_con,
                                            'frame': n.product_id.frame,
                                            'acc': n.product_id.acc,
                                            'speed': n.product_id.speed,
                                            'speed_uom_id': n.product_id.speed_uom_id,
                                            'speed_dr': n.product_id.speed_dr,
                                            'speed_uom_id_dr': n.product_id.speed_uom_id_dr,
                                            'rate_dr': n.product_id.rate_dr,
                                            'rate_uom_id_dr': n.product_id.rate_uom_id_dr,
                                            'rate_con': n.product_id.rate_con,
                                            'rate_uom_id_con': n.product_id.rate_uom_id_con,
                                            'Pro_type': n.product_id.Pro_type,
                                            'Pro_type_dr': n.product_id.Pro_type_dr,
                                            'Pro_type_con': n.product_id.Pro_type_con,
                                            'bom_ok':n.product_id.bom_ok,
                                            'Pro_type_ger': n.product_id.Pro_type_ger,
                                            'Type_ger' : n.product_id.Type_ger,
                                            'manu_gear' : n.product_id.manu_gear,
                                            'model_gear' : n.product_id.model_gear,
                                            'ratio_gear' : n.product_id.ratio_gear,
                                            'approval_gear' : n.product_id.approval_gear,
                                            'no_of_stages' : n.product_id.no_of_stages,
                                            'material_spec' : n.product_id.material_spec,
                                            'spare_part' : n.product_id.spare_part,
                                            'site_voltage' : n.product_id.site_voltage,
                                            'with_ats' : n.product_id.with_ats,
                                            'special_options' : n.product_id.special_options,
                                            'watertank' : n.product_id.watertank,
                                            'pressuge_gauge' : n.product_id.pressuge_gauge,
                                            'waste_cone' : n.product_id.waste_cone,
                                            'flame_arrester' : n.product_id.flame_arrester,
                                            'remote_alarm' : n.product_id.remote_alarm,
                                            'charger_voltage' : n.product_id.charger_voltage,
                                            'silencer_type' : n.product_id.silencer_type,
                                            'prv' : n.product_id.prv,
                                            'fuel_tank' : n.product_id.fuel_tank,
                                            'derating' : n.product_id.derating,
                                            }
                        invoice_line.append((0, 0, invoice_line_vals))
                        vals = ({'sale_order_option_ids': invoice_line})
                    else:
                        raise UserError(_('This BOM %s is duplicate in this main product %s and it should be having unique BOMs ') % (n.product_id.code,com.product_tmpl_id.default_code))
        super(sale_wf_inherit, self).update(vals)

    # @api.multi
    # @api.depends('sale_order_option_ids')
    # def _com_sub_items(self):
    #     vals = {}
    #     invoice_line = []
    #     i = 0
    #     for rec in self:
    #         for l in rec.sale_order_option_ids:
    #             i = i + 1
    #             # raise ValidationError(_(l.product_id.code))
    #             com = self.env['mrp.bom'].search([('product_tmpl_id','=',l.product_id.code)])
    #             # com = com.read([])
    #             if not com:
    #                 break
    #             if not com.bom_line_ids:
    #                 continue
    #             else:
    #                 for n in com.bom_line_ids:
    #                     invoice_line_vals = {'product_id': n.product_id,
    #                                         'name':n.product_id.name,
    #                                         'uom_id':n.product_uom_id,
    #                                         'quantity':n.product_qty,
    #                                         'num': i,
    #                                         'check': 0,
    #                                         'flow': n.product_id.flow,
    #                                         'flow_uom_id': n.product_id.flow_uom_id,
    #                                         'head': n.product_id.head,
    #                                         'Type': n.product_id.Type,
    #                                         'manu': n.product_id.manu,
    #                                         'model': n.product_id.model,
    #                                         'listing': n.product_id.listing,
    #                                         'con': n.product_id.con,
    #                                         'supply': n.product_id.supply,
    #                                         'enc': n.product_id.enc,
    #                                         'frame': n.product_id.frame,
    #                                         'acc': n.product_id.acc,
    #                                         'speed': n.product_id.speed,
    #                                         'speed_uom_id': n.product_id.speed_uom_id,
    #                                         'rate': n.product_id.rate,
    #                                         'rate_uom_id': n.product_id.rate_uom_id,
    #                                         'Pro_type': n.product_id.Pro_type,
    #                                         }
    #                     invoice_line.append((0, 0, invoice_line_vals))
    #                     vals = ({'sale_order_options_ids': invoice_line})
    #         super(sale_wf_inherit, self).update(vals)


class product_inh(models.Model):
    _inherit = 'product.template'

    bom_ok = fields.Boolean('Is BOM Item')
    flow = fields.Float('Pump Flow')
    flow_uom_id = fields.Many2one('uom.uom',string="Pump Flow UOM")
    head = fields.Char('Pump Head')
    Pro_type = fields.Char('Pump Product Type')
    Pro_type_dr = fields.Char('Driver Product Type')
    Pro_type_con = fields.Char('Controller Product Type')
    Type = fields.Char('Pump Type')
    Type_dr = fields.Char('Driver Type')
    Type_con = fields.Char('Controller Type')
    manu = fields.Char('Pump Manufacture')
    manu_dr = fields.Char('Driver Manufacture')
    manu_con = fields.Char('Controller Manufacture')
    model = fields.Char('Pump Model')
    model_dr = fields.Char('Driver Model')
    listing = fields.Char('Pump Listing')
    listing_dr = fields.Char('Driver Listing')
    listing_con = fields.Char('Controller Listing')
    con = fields.Char('Pump Construction')
    supply_dr = fields.Char('Driver Supply')
    supply_con = fields.Char('Controller Supply')
    enc_dr = fields.Char('Driver Enclosure')
    enc_con = fields.Char('Controller Enclosure')
    frame = fields.Char('Driver Frame Size')
    acc = fields.Char('Pump Accessories')
    speed = fields.Float('Pump Speed')
    speed_uom_id = fields.Many2one('uom.uom',string="Pump Speed UOM")
    speed_dr = fields.Float('Driver Speed')
    speed_uom_id_dr = fields.Many2one('uom.uom',string="Driver Speed UOM")
    rate_dr = fields.Float('Driver Rating')
    rate_uom_id_dr = fields.Many2one('uom.uom',string="Driver Rating UOM")
    rate_con = fields.Float('Controller Rating')
    rate_uom_id_con = fields.Many2one('uom.uom',string="Controller Rating UOM")

    po_noo = fields.Float('Reserved')
    po_noo2 = fields.Float('Reserved')
    poo_ref = fields.Char('PO Referance')
    poo_ref2 = fields.Char('PO Referance')
    forcaste_num = fields.Float('Forcaste Qty',compute='_get_computed_fields')
    po_num = fields.Float('Qty In Open POs',compute='_get_computed_fields')
    po_name = fields.Char('Name Of Open POs',default=' - ')
    so_num = fields.Float('Qty In Open SOs',compute='_get_computed_fields')
    so_name = fields.Char('Name Of Open SOs',default=' - ')
    mo_num = fields.Float('Qty In Open MOs',compute='_get_computed_fields')
    mo_name = fields.Char('Name Of Open MOs',default=' - ')
    mo_no = fields.Float('Reserved')
    mo_no_total = fields.Float('Reserved')
    mo_no_total2 = fields.Float('Reserved',compute='_get_computed_fields')
    mo_ref = fields.Char('MO Referance')
    poo_name = fields.Char('Name Of Done POs',default=' - ')
    op_po_no = fields.Float('Reserved')
    op_po_ref = fields.Char('PO Referance')
    moo_name = fields.Char('Name Of Done MOs',default=' - ')
    moo_qty = fields.Char('Quantity')
#   start add By fouad  Controller Product Type

    no_of_stages = fields.Char('No Of Stages')
    Pro_type_ger = fields.Char('Gear Driver')
    Type_ger = fields.Char('Gear Type')
    manu_gear = fields.Char('Gear Manufacture') 
    model_gear = fields.Char('Gear Model')
    ratio_gear = fields.Char('Gear Ratio')
    approval_gear = fields.Char('Gear Approval')
#   end add By fouad

# new changes ziad 

    # pump
    material_spec = fields.Char("Add'l Material Spec")
    spare_part = fields.Char("Spare Parts")
    # pump
    # driver
    fuel_tank = fields.Char("Fuel Tank Capacity")
    prv = fields.Char("PRV")
    silencer_type = fields.Char("Silencer Type")
    derating = fields.Char("Derating")
    # driver
    # Controller
    site_voltage = fields.Char("Site Voltage")
    charger_voltage = fields.Char("Charger Voltage")
    with_ats = fields.Char("With ATS")
    special_options = fields.Char("Special Options")
    # Controller
    # gear driver
    watertank = fields.Char("Watertank Depth")
    # gear driver
    # special options
    pressuge_gauge = fields.Selection(string='Pressuge Gauge', selection=[
        ('stand','Standard'),
        ('liqu','Liquid Filled')])
    waste_cone = fields.Char("Waste Cone")
    flame_arrester = fields.Char("Flame Arrester")
    remote_alarm = fields.Char("Remote Alarm")
    service_to_purchase = fields.Boolean("Purchase Automatically",default=False, help="If ticked, each time you sell this product through a SO, a RfQ is automatically created to buy the product. Tip: don't forget to set a vendor on the product.")

    Product_arabic = fields.Text('Product Name Arabic')
    # special options
# new changes ziad 


   # default_code = fields.Char(
   #     'Internal Reference', compute='_compute_default_code',
   #     inverse='_set_default_code', store=True,required=True)

    # @api.onchange('name')
    # # @api.onchange('default_code','name')
    # def _name_con(self):
    #     for l in self:
    #         com = self.env['product.template'].search([('name','=',l.name)])
    #         if com:
    #             raise ValidationError(_('This Name already used, The product name should be unique!'))
    #         else:
    #             continue

#    @api.onchange('default_code')
#    def _code_con(self):
#        for l in self:
#            com = self.env['product.template'].search([('default_code','=',l.default_code),('default_code','!=','')])
#            if com:
#                if com.default_code:
#                    raise ValidationError(_('this Referance they should be unique'))
#                else:
#                    break
#            else:
#                continue



    _sql_constraints = [
    ('default_code_unique', 'unique(default_code)', 'Internal reference already exists! Choose anthor one')
    ]

    @api.model_cr
    def _get_computed_fields(self,context=None):
        for rec in self:
            
            self.env.cr.execute("""select
                                ( SELECT COALESCE(sum(sm.product_uom_qty),0) AS sum FROM stock_move sm
                                join mrp_production mp on mp.id=sm.raw_material_production_id
                                WHERE mp.state not in ('done','cancel') and sm.raw_material_production_id is not null and sm.product_id=pp.id) AS mo_num,

                                ( SELECT COALESCE(sum(sm.product_uom_qty),0) AS sum FROM stock_move sm
                                WHERE sm.state not in ('done','cancel') and sm.picking_type_id=1 and sm.product_id=pp.id) AS po_num,
                                
                                ( SELECT COALESCE(sum(sm.product_uom_qty),0) AS sum FROM stock_move sm
                                WHERE sm.state not in ('done','cancel') and sm.picking_type_id=2 and sm.product_id=pp.id) AS so_num, 
                                
                                ( SELECT COALESCE(sum(sq.quantity),0) AS sum FROM stock_quant sq
                                join stock_location sl on sl.id=sq.location_id
                                where sl.usage='internal' and sq.product_id=pp.id) AS qty_on_hand,

                                ( SELECT COALESCE(sum(sq.reserved_quantity),0) AS sum FROM stock_quant sq
                                join stock_location sl on sl.id=sq.location_id
                                where sl.usage='internal' and sq.product_id=pp.id) AS total_reserved,
                                
                                ( SELECT COALESCE(sum(sq.reserved_quantity),0) AS sum FROM stock_quant sq
                                join stock_location sl on sl.id=sq.location_id
                                where sl.usage='internal' and sl.id not in (18,19) and sq.product_id=pp.id) AS mo_no_total2,

                                (( SELECT COALESCE(sum(sq.quantity),0) AS sum FROM stock_quant sq
                                join stock_location sl on sl.id=sq.location_id
                                where sl.usage='internal' and sq.product_id=pp.id)- ( SELECT COALESCE(sum(sm.product_uom_qty),0) AS sum FROM stock_move sm
                                join mrp_production mp on mp.id=sm.raw_material_production_id
                                WHERE mp.state not in ('done','cancel') and sm.raw_material_production_id is not null and sm.product_id=pp.id)-( SELECT COALESCE(sum(sm.product_uom_qty),0) AS sum FROM stock_move sm
                                WHERE sm.state not in ('done','cancel') and sm.picking_type_id=2 and sm.product_id=pp.id))as forcaste_num
                                FROM product_product pp
                                join product_template pt on pt.id=pp.product_tmpl_id 
                                where pt.active='t' and pt.id=%s
                                order by pt.id
                """ % (rec.id))
            res = self.env.cr.dictfetchall() 
            # raise UserError(res)
            for x in res:
                rec.mo_num = x['mo_num'] or 0.0
                rec.so_num = x['so_num'] or 0.0
                rec.po_num = x['po_num'] or 0.0
                rec.mo_no_total2 = x['mo_no_total2'] or 0.0
                rec.forcaste_num = x['forcaste_num'] or 0.0
                # raise UserError("""%s %s %s %s"""% (x['mo_num'],x['so_num'],x['po_num'],x['mo_no_total2']))

    @api.multi
    @api.depends('default_code')
    def _compute_field(self):
        for rec in self:
            inv_obj = self.env['purchase.report.one']
            po = ''
            # com = self.env['purchase.order'].search([('state','=',['draft','send'])])
            # rec.po_num = 0
            # rec.op_po_no = 0
            # for l in com:
            #     for line in l.order_line:
            #         if rec.default_code == line.product_id.code and rec.name == line.product_id.name:
            #             rec.po_num = rec.po_num + line.product_qty
            #             po = po + '   ' +  str(l.name)
            #             rec.op_po_no = line.product_qty
            #             rec.op_po_ref = l.name
            #             cod = self.env['purchase.report.one'].search([('op_po_ref','=',rec.op_po_ref),('product_id','=',rec.default_code)])
            #             # if cod:
            #             #     raise UserError(_(cod))
            #             if not cod:
            #                 # raise UserError(_('empty'))
            #                 inv_obj.create({'op_po_no': rec.op_po_no,'op_po_ref':rec.op_po_ref,'product_id':rec.id})
            # rec.po_name = po

            # ???????????????????????????????????????????????????????????????????????????????????????????????????
            
            com = self.env['stock.picking'].search([('picking_type_id','=',1)])
            y = 0.0
            x = 0.0
            
            if com:
                for line in com:
                    if line.state == 'done':
                        cos = self.env['purchase.report.one'].search([])
                        for k in cos:
                            if k.op_po_ref2 == line.name :
                                k.unlink()
                    elif line.state == 'cancel':
                        cos = self.env['purchase.report.one'].search([])
                        for k in cos:
                            if k.op_po_ref2 == line.name :
                                k.unlink()

                    else:
                        for l in line.move_ids_without_package:
                            if rec.default_code == l.product_id.default_code:
                                if l.quantity_done >= l.product_uom_qty:
                                    
                                    continue
                                else:
                                    y = l.product_uom_qty - l.quantity_done
                                    x = x + y
                                    rec.op_po_ref = line.origin
                                    rec.op_po_no = y
                                    cod = self.env['purchase.report.one'].search([('op_po_ref2','=',line.name),('product_id','=',rec.default_code)])
                                    if cod:
                                        for k in cod:
                                            k.write({'op_po_no': rec.op_po_no})
                                    if not cod:
                                        # raise UserError(_('empty'))
                                        inv_obj.create({'op_po_no': rec.op_po_no,'op_po_ref':rec.op_po_ref,'op_po_ref2':line.name,'product_id':rec.id})

                # rec.po_num = x
                # raise UserError(_(rec.po_name))



    @api.multi
    @api.depends('default_code')
    def _compute_fieldso(self):
        for rec in self:
            inv_obj = self.env['purchase.report.tw']
            # po = ''
            # com = self.env['sale.order'].search([('state','=',['sale','draft','send','approve'])])
            # rec.so_num = 0
            # for l in com:
            #     for line in l.order_line:
            #         if rec.default_code == line.product_id.code and rec.name == line.product_id.name:
            #             rec.so_num = rec.so_num + line.product_uom_qty
            #             po = po + '   ' +  str(l.name)
            # rec.so_name = po
            # inv_obj = self.env['purchase.report.one']
            
            com = self.env['stock.picking'].search([('picking_type_id','=',2)])
            y = 0.0
            x = 0.0
            
            if com:
                for line in com:
                    if line.state == 'done':
                        cos = self.env['purchase.report.tw'].search([])
                        for k in cos:
                            if k.poo_ref2 == line.name :
                                k.unlink()
                    elif line.state == 'cancel':
                        cos = self.env['purchase.report.tw'].search([])
                        for k in cos:
                            if k.poo_ref2 == line.name :
                                k.unlink()

                    else:
                        for l in line.move_ids_without_package:
                            if rec.default_code == l.product_id.default_code:
                                if l.quantity_done >= l.product_uom_qty:
                                    
                                    continue
                                else:
                                    y = l.product_uom_qty - l.quantity_done
                                    x = x + y
                                    rec.poo_ref = line.origin
                                    rec.po_noo = y
                                    cod = self.env['purchase.report.tw'].search([('poo_ref2','=',line.name),('product_id','=',rec.default_code)])
                                    if cod:
                                        for k in cod:
                                            k.write({'po_noo': rec.po_noo})
                                    if not cod:
                                        # raise UserError(_('empty'))
                                        inv_obj.create({'po_noo': rec.po_noo,'poo_ref':rec.poo_ref,'poo_ref2':line.name,'product_id':rec.id})

                # rec.so_num = x



    # @api.multi
    # @api.depends('default_code')
    # def _compute_forcaste(self):
    #     for rec in self:
    #         rec.forcaste_num = rec.qty_available - rec.mo_num - rec.so_num
            




    @api.multi
    @api.depends('default_code')
    def _compute_fieldmo(self):
        for rec in self:
            inv_obj = self.env['manufacture.report.tw']
            # po = ''
            # com = self.env['sale.order'].search([('state','=',['sale','draft','send','approve'])])
            # rec.so_num = 0
            # for l in com:
            #     for line in l.order_line:
            #         if rec.default_code == line.product_id.code and rec.name == line.product_id.name:
            #             rec.so_num = rec.so_num + line.product_uom_qty
            #             po = po + '   ' +  str(l.name)
            # rec.so_name = po
            # inv_obj = self.env['purchase.report.one']
            
            com = self.env['mrp.production'].search([])
            y = 0.0
            x = 0.0
            
            if com:
                for line in com:
                    if line.state == 'done':
                        cos = self.env['manufacture.report.tw'].search([])
                        for k in cos:
                            if k.poo_ref2 == line.name :
                                k.unlink()
                    elif line.state == 'cancel':
                        cos = self.env['manufacture.report.tw'].search([])
                        for k in cos:
                            if k.poo_ref2 == line.name :
                                k.unlink()
                    else:
                        for l in line.move_raw_ids:
                            lot_no = ''
                            if l.active_move_line_ids:
                                # lot_no = ''
                                for k in l.active_move_line_ids:
                                    # if len(k) == 1:
                                    # lot_no = k.lot_id.name
                                # else:
                                    
                                    if k.lot_id:
                                        lot_no = lot_no + '  \n ' + str(k.lot_id.name)
                                    else:
                                        continue
                            if rec.default_code == l.product_id.default_code:
                                if l.product_uom_qty == 0.0 :
                                    continue
                                else:
                                    y = l.product_uom_qty
                                    x = x + y
                                    rec.poo_ref = line.origin
                                    rec.po_noo2 = y
                                    cod = self.env['manufacture.report.tw'].search([('poo_ref2','=',line.name),('product_id','=',rec.default_code)])
                                    if cod:
                                        for k in cod:
                                            k.write({'po_noo': rec.po_noo2,'lot_no':lot_no})
                                    if not cod:
                                        # raise UserError(_('empty'))
                                        inv_obj.create({'po_noo': rec.po_noo2,'poo_ref':rec.poo_ref2,'poo_ref2':line.name,'lot_no':lot_no,'product_id':rec.id})
                # rec.mo_num = x


    @api.multi
    @api.depends('default_code')
    def _compute_fieldmo_pro(self):
        inv_obj = self.env['report.stock.forecast.two']
        for rec in self:
            po = ''
            no = ''
            # com = self.env['mrp.production'].search([('state','=','done')])
            com = self.env['stock.picking'].search(['|',('picking_type_id','=',6),('picking_type_id','=',2)])
            rec.mo_no = 0
            rec.mo_no_total2 = 0
            y = 0.0
            x = 0.0
            
            if com :
                for n in com:
                    if n.picking_type_id.id == 6 :
                        
                        if n.state == 'cancel':
                            cos = self.env['report.stock.forecast.two'].search([])
                            for k in cos:
                                if k.mo_ref2 == n.name :
                                    k.unlink()
                        elif n.state == 'done':
                            cos = self.env['report.stock.forecast.two'].search([])
                            for k in cos:
                                if k.mo_ref2 == n.name :
                                    k.unlink()
                        else:
                            for l in n.move_ids_without_package:
                                if l.move_line_ids:
                                    lot_no = ''
                                    for k in l.move_line_ids:
                                        # if len(k) == 1:
                                        # lot_no = k.lot_id.name
                                    # else:
                                        
                                        lot_no = lot_no + '  \n ' + str(k.lot_id.name)
                                    

                                if rec.default_code == l.product_id.default_code:
                                    # if l.reserved_availability == 0.0 :
                                    
                                        # raise UserError(_(l.product_id.code))
                                        # rec.mo_no_total = rec.mo_no_total + l.quantity_done
                                    if l.reserved_availability == 0.0 :
                                        continue
                                    else:
                                        y = l.reserved_availability
                                        x = x + y
                                        rec.mo_no = y
                                        rec.mo_ref = n.origin
                                        po = po + ' \n  ' + str(n.origin)
                                        no = no + '  \n ' + str(l.reserved_availability)
                        #	rec.mo_no_total = rec.mo_no + rec.mo_no_total
                                        cod = self.env['report.stock.forecast.two'].search([('mo_ref2','=',n.name),('product_id','=',rec.default_code)])
                                        if not cod:
                                            inv_obj.create({'mo_no': rec.mo_no,'mo_ref':rec.mo_ref,'mo_ref2':n.name,'lot_no':lot_no,'product_id':rec.id})
                                        if cod:
                                            for k in cod:
                                                if k.mo_ref2 == n.name and rec.mo_no == 0:
                                                    k.unlink()
                                                else:
                                                    k.write({'mo_no': rec.mo_no,'lot_no':lot_no})                                # raise UserError(_('empty'))
                    else:
                        if n.state == 'cancel':
                            cos = self.env['report.stock.forecast.two'].search([])
                            for k in cos:
                                if k.mo_ref2 == n.name :
                                    k.unlink()
                        elif n.state == 'done':
                            cos = self.env['report.stock.forecast.two'].search([])
                            for k in cos:
                                if k.mo_ref2 == n.name :
                                    k.unlink()

                        else:
                            for l in n.move_ids_without_package:
                                if l.move_line_ids:
                                    lot_no = ''
                                    for k in l.move_line_ids:
                                        # if len(k) == 1:
                                        # lot_no = k.lot_id.name
                                    # else:
                                        
                                        lot_no = lot_no + '  \n ' + str(k.lot_id.name)
                                if rec.default_code == l.product_id.default_code:
                                    # if l.quantity_done >= l.product_uom_qty:
                                        
                                        # continue
                                    # else:
                                    if l.reserved_availability == 0.0 :
                                        continue
                                    else:
                                        y = l.reserved_availability
                                        x = x + y
                                        rec.mo_ref = n.origin
                                        rec.mo_no = y
                                        cod = self.env['report.stock.forecast.two'].search([('mo_ref2','=',n.name),('product_id','=',rec.default_code)])
                                        if not cod:
                                            inv_obj.create({'mo_no': rec.mo_no,'mo_ref':rec.mo_ref,'mo_ref2':n.name,'lot_no':lot_no,'product_id':rec.id})
                                        if cod:
                                            for k in cod:
                                                if k.mo_ref2 == n.name and rec.mo_no == 0:
                                                    k.unlink()
                                                else:
                                                    k.write({'mo_no': rec.mo_no,'lot_no':lot_no})
            # raise UserError(_(rec.name))
                # rec.mo_no_total2 = x 
            # rec.moo_name = po
            # rec.moo_qty = no
    
    # reserverd qty
    @api.multi
    @api.depends('default_code')
    def _compute_reserved(self):
        # inv_obj = self.env['report.stock.forecast.two']
        for rec in self:
            # po = ''
            no = 0
            # noo = ''
            com = self.env['stock.quant'].search([('product_id','=',rec.default_code),('location_id','=',12)])
            for l in com:
                # rec.mo_ref = l.id
                # rec.mo_no = l.reserved_quantity
                no = no + l.reserved_quantity
                # cod = self.env['report.stock.forecast.two'].search([('mo_ref','=',rec.mo_ref),('product_id','=',rec.default_code)])
                # if not cod:
                    # inv_obj.create({'mo_no': rec.mo_no,'mo_ref':rec.mo_ref,'product_id':rec.id})
            rec.mo_no_total = no

    def action_open_mos(self):
        action = self.env.ref('wf_updates.action_stock_level_forecast_report_template_two').read()[0]
        return action

    def action_open_pos(self):
        for rec in self:
            inv_obj = self.env['purchase.report.tw']
            values = []
            self.env.cr.execute("""delete from purchase_report_tw where product_id=%s """ % (rec.id))
            self.env.cr.execute("""SELECT  
                                    sm.product_id as product,
                                    sm.product_uom_qty as qty,
                                    sm.picking_id as pick,
                                    sm.date_expected as expected_date,
                                    sm.origin as ref
                                    FROM stock_move sm
                                    join product_product pp on pp.id=sm.product_id
                                    join product_template pt on pt.id=pp.product_tmpl_id
                                    WHERE sm.state not in ('done','cancel') and sm.picking_type_id=2 and pt.id=%s
                """ % (rec.id))
            res = self.env.cr.dictfetchall() 
            # raise UserError(res)
            for x in res:
                vals = {'po_noo': x['qty'],'poo_ref':x['ref'],'pick':x['pick'],'product_id':rec.id}
                values.append(vals)
            inv_obj.create(values)
        action = self.env.ref('wf_updates.action_view_purchase_report_tree0').read()[0]
        return action

    def action_open_oppos(self):
        for rec in self:
            inv_obj = self.env['purchase.report.one']
            values = []
            self.env.cr.execute("""delete from purchase_report_one where product_id=%s """ % (rec.id))
            self.env.cr.execute("""SELECT 
                                    sm.product_id as product,
                                    sm.product_uom_qty as qty,
                                    sm.picking_id as pick,
                                    sm.date_expected as expected_date,
                                    po.name as ref,
                                    po.date_order as po_order_date
                                    FROM stock_move sm
                                    join purchase_order_line p_line on p_line.id=sm.purchase_line_id
                                    join purchase_order po on po.id=p_line.order_id
                                    join product_product pp on pp.id=sm.product_id
                                    join product_template pt on pt.id=pp.product_tmpl_id
                                    WHERE sm.state not in ('done','cancel') and sm.picking_type_id=1 and pt.id=%s
                """ % (rec.id))
            res = self.env.cr.dictfetchall() 
            # raise UserError(res)
            for x in res:
                vals = {'op_po_no': x['qty'],'op_po_ref':x['ref'],'product_id':rec.id}
                values.append(vals)
            inv_obj.create(values)
        action = self.env.ref('wf_updates.action_view_purchase_report_tree2').read()[0]
        return action

    @api.model_cr
    def action_open_moss(self):
        for rec in self:
            inv_obj = self.env['manufacture.report.tw']
            values = []
            self.env.cr.execute("""delete from manufacture_report_tw where product_id=%s """ % (rec.id))
            self.env.cr.execute("""SELECT 
                                    mp.name as ref,
                                    mp.origin as origin,
                                    sm.state as state,
                                    sm.product_id as product,
                                    sm.product_uom_qty as qty,
                                    --sml.lot_id as lot
                                    (select string_agg( spl.name, ',')
                                        from stock_move_line sml
                                        join stock_production_lot spl on spl.id=sml.lot_id
                                        where sml.move_id=sm.id and sml.lot_id is not null) as lot_no
                                    FROM 	stock_move sm,
                                        product_product pp ,
                                        product_template pt,
                                        mrp_production mp
                                    WHERE 	pp.id=sm.product_id
                                    and 	pt.id=pp.product_tmpl_id
                                    and 	mp.id=sm.raw_material_production_id
                                    and 	mp.state not in ('done','cancel') 
                                    and 	pt.id=%s
                """ % (rec.id))
            res = self.env.cr.dictfetchall() 

            for x in res:
                vals = {'po_noo': x['qty'],'poo_ref':x['origin'],'state':x['state'],'lot_no':x['lot_no'],'poo_ref2':x['ref'],'product_id':rec.id}
                values.append(vals)
            inv_obj.create(values)
        action = self.env.ref('wf_updates.action_view_manufacture_report_tree0').read()[0]
        return action
            
    
class report_stock_forecast_inherit(models.Model):
    _name = "report.stock.forecast.two"

    mo_no = fields.Char('Reserved')
    mo_ref = fields.Char('MO Referance',invisible=True)
    mo_ref2 = fields.Char('MO Referance',invisible=True)
    lot_no = fields.Char('Lot/Serial Number')
    product_id = fields.Many2one('product.template',string='Product')


class purchase_report_tw_inherit(models.Model):
    _name = "purchase.report.tw"

    po_noo = fields.Char('Done Qty')
    poo_ref = fields.Char('SO Reference')
    pick = fields.Many2one('stock.picking',string='Picking Reference')
    poo_ref2 = fields.Char('SO Reference')
    product_id = fields.Many2one('product.template',string='Product')

class manufacture_report_tw_inherit(models.Model):
    _name = "manufacture.report.tw"

    po_noo = fields.Char('Done Qty')
    poo_ref = fields.Char('Main Source')
    state = fields.Char('State')
    poo_ref2 = fields.Char('MO Reference')
    lot_no = fields.Char(string='Lot/Serial Number')
    product_id = fields.Many2one('product.template',string='Product')

class purchase_report_one_inherit(models.Model):
    _name = "purchase.report.one"

    op_po_no = fields.Char('Qty')
    op_po_ref = fields.Char('Open PO Reference')
    op_po_ref2 = fields.Char('Open PO Reference')
    product_id = fields.Many2one('product.template',string='Product')

class crm_wf_inherit(models.Model):
    _inherit = "crm.lead"

    project_name = fields.Char('Project Name')
    consultant_name = fields.Char('Consultant Name')

class pur_order_inherit(models.Model):
    _inherit = "purchase.order"

    des = fields.Char('Destination')
    delivery_term = fields.Char('Delivery Terms')
    old = fields.Char('Old Reference')
    text = fields.Char('Price in Text',compute="_com_price2",invisible=True)
    entire = fields.Char('Price in Text',compute="_com_price")
    decimal = fields.Char('Price in Text',compute="_com_price")
    revsion_check = fields.Boolean('Revise PO',default=False)
    revsion_ref = fields.Char('Rev. No.')
    totalqty = fields.Float('Total of qty',compute="_com_qty")
    receive_state = fields.Selection(string='Current State', selection=[
        ('New','New'),
        ('Ready','Ready'),
        ('Partial Receive','Partial Receive'),
        ('Closed','Closed')],
        copy=False, index=True, readonly=True,compute="ready_state")
    curr_change_untaxed = fields.Float('Untaxed Amount in AED',compute='_amount_change')
    curr_change_total = fields.Float('Total Amount in AED',compute='_amount_change')
    purpose = fields.Text('Purpose')
    department_id = fields.Many2one('hr.department',string='Department')

    # by Fouad For comparsion report ----------------------------------------

    total_price = fields.Float('product price',compute='_get_data')

    @api.model
    def _cancel_auto_rfq(self):
        com = self.env['purchase.order'].search([('user_id','=',1),('state','!=','cancel')])
        for rec in com:
            rec.button_cancel()
        

    @api.multi
    def _get_data(self):
        for rec in self:
            for l in rec.order_line :
                record = []
                # vender = []
                # price = []
                record_collection = self.env['product.product'].search([('id', '=', l.product_id.id)])
                if len(record_collection) > 0:
                    for lin in record_collection:
                        com = lin.seller_ids
                        for x in com :
                            for v in x :
                                vaul = {
                                'name' : v.name,
                                'price' : v.price,
                                'total' : l.product_qty * x.price ,
                                'discount' : v.payment_terms ,
                                'total_cost' : v.payment_terms,
                                'payment_terms' : v.payment_terms ,
                                'warranty' : v.warranty ,
                                'delivery_terms' : v.delivery_terms ,
                                'delay' : v.delay ,
                                }
                                record.append(vaul)
               
                
        return record 

    # end  by Fouad ----------------------------------------------------------------


    @api.multi
    def _amount_change(self):
        for rec in self:
            currency = rec.currency_id
            rec.curr_change_total = currency._convert(rec.amount_total, self.env.user.company_id.currency_id, self.env.user.company_id, rec.date_order or date.today())
            rec.curr_change_untaxed = currency._convert(rec.amount_untaxed, self.env.user.company_id.currency_id, self.env.user.company_id, rec.date_order or date.today())
            


    @api.multi
    def _com_qty(self):
        for rec in self:
            x = 0.0
            for line in rec.order_line:
                x = x + line.product_qty
            rec.totalqty = x

    @api.multi
    @api.depends('date_planned')
    def ready_state(self):
        current_date = date.today()
        for rec in self:
        # raise UserError(_(self.date_planned.date()))
            if (rec.state == 'draft','sent','to approve') and (rec.date_planned.date() > current_date):
                rec.receive_state = 'New'
            if (rec.date_planned.date() <= current_date):
                rec.receive_state = 'Ready'
            if rec.state == 'purchase':
                # rec.receive_state = 'part'
                com = self.env['stock.picking'].search([('origin','=',rec.name)])
                if len(com) == 1:
                    for line in com:
                        if line.state == 'done':
                            rec.receive_state = 'Closed'
                        else:
                            y = 0
                            x = 0
                            z = len(line.move_ids_without_package)
                            for l in line.move_ids_without_package:
                                if l.product_uom_qty == l.quantity_done:
                                    y = y + 1
                                    continue
                                else:
                                    x = x + 1
                            if z == x:
                                if (rec.date_planned.date() <= current_date):
                                    rec.receive_state = 'Ready'
                                else:
                                    rec.receive_state = 'New'
                            else:
                                rec.receive_state = 'Partial Receive'
                else:
                    for line in com:
                        if line.state != 'done':
                            rec.receive_state = 'Partial Receive'
                            break
                        else:
                            rec.receive_state = 'Closed'

    @api.multi
    def _com_price(self):
        # self.text = num2words(self.amount_total, lang='en')
        pre = float(self.amount_total)
        text1 = ''
        entire_num = int((str(pre).split('.'))[0])
        decimal_num = int((str(pre).split('.'))[1])
        if decimal_num < 10:
            decimal_num = decimal_num * 10        
        text1+=num2words(entire_num, lang='en')
        self.entire = num2words(entire_num, lang='en')
        self.entire = self.entire.replace(' and ', ' ')
        text1+=' and '
        text1+=num2words(decimal_num, lang='en')
        self.decimal = num2words(decimal_num, lang='en')
        # self.text = text1

    @api.depends('amount_total','currency_id')
    def _com_price2(self):
        # res = super(pur_order_inherit, self)._onchange_amount()
        self.text = self.currency_id.amount_to_text(self.amount_total) if self.currency_id else ''
        self.text = self.text.replace(' And ', ' ')
        

    # @api.onchange('amount_total','currency_id')
    # def _onchange_amount(self):
    #     res = super(pur_order_inherit, self)._onchange_amount()
    #     self.text = self.currency_id.amount_to_text(self.amount_total) if self.currency_id else ''
    #     return res

class mrp_production_inherit(models.Model):
    _inherit = "mrp.production"

    old = fields.Char('Old Reference')
    worker_order_number = fields.Char('Work Order No.')
    pump_serial_no = fields.Char('Pump Serial No.')
    impeller_size_1 = fields.Char('Impeller Size -1')
    impeller_size_2 = fields.Char('Impeller Size -2')
    impeller_size_3 = fields.Char('Impeller Size -3')
    impeller_size_4 = fields.Char('Impeller Size -4')
    skid_size = fields.Char('Skid Size.')
    coupling_model = fields.Char('Coupling Model')
    coupling_guard = fields.Char('Coupling Guard')
    riser = fields.Char('Riser')
    remark = fields.Text('REMARKS')
    customer_name = fields.Many2one('res.partner','Customer Name',compute='_get_customer')

    @api.multi
    @api.depends('origin')
    def _get_customer(self):
        for rec in self:
            if rec.origin:
                if rec.origin[:2] == 'SO':
                    com = self.env['sale.order'].search([('name','=',rec.origin)])
                    rec.customer_name = com.partner_id
                else:
                    com = self.env['mrp.production'].search([('name','=',rec.origin)])
                    so = self.env['sale.order'].search([('name','=',com.origin)])
                    rec.customer_name = so.partner_id

class stock_move_inherit(models.Model):
    _inherit = "stock.move"

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[], index=True, required=True,
        states={'done': [('readonly', True)]})

    def unlink(self):
        # if any(move.state not in ('draft', 'cancel') for move in self):
            # raise UserError(_('You can only delete draft moves.'))
        # With the non plannified picking, draft moves could have some move lines.
        self.mapped('move_line_ids').unlink()
        return super(stock_move_inherit, self).unlink()

class AccountMoveCus(models.Model):
    _inherit = "account.move"

    @api.multi
    def assert_balanced(self):
        if not self.ids:
            return True

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self._cr.execute('''
            SELECT line.move_id, ROUND(SUM(line.debit - line.credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(line.debit - line.credit), currency.decimal_places) != 0.0;
        ''', [tuple(self.ids)])

        res = self._cr.fetchone()
        # if res:
            # raise UserError(
                # _("Cannot create unbalanced journal entry.") +
                # "\n\n{}{}".format(_('Difference debit - credit: '), res[1])
            # )
        return True




class stock_line_inherit(models.Model):
    _inherit = "stock.move.line"

    onhand = fields.Float('Onhand',compute="_com_hand")

    @api.multi
    @api.depends('product_id')
    def _com_hand(self):
        for rec in self:
            com = self.env['product.template'].search([('id','=',rec.product_id.product_tmpl_id.id)])
            rec.onhand = com.qty_available

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# Inventory Adjustment approval

class stock_inventory_inherit(models.Model):
    _inherit = "stock.inventory"

    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('approve','To Approve'),
        ('confirm', 'In Progress'),
        ('done', 'Validated')],
        copy=False, index=True, readonly=True,
        default='draft')

    @api.multi
    def action_validate(self):
        return self.write({'state': 'approve'})

    @api.multi
    def button_approve(self, force=False):
        inventory_lines = self.line_ids.filtered(lambda l: l.product_id.tracking in ['lot', 'serial'] and not l.prod_lot_id and l.theoretical_qty != l.product_qty)
        lines = self.line_ids.filtered(lambda l: float_compare(l.product_qty, 1, precision_rounding=l.product_uom_id.rounding) > 0 and l.product_id.tracking == 'serial' and l.prod_lot_id)
        if inventory_lines and not lines:
            wiz_lines = [(0, 0, {'product_id': product.id, 'tracking': product.tracking}) for product in inventory_lines.mapped('product_id')]
            wiz = self.env['stock.track.confirmation'].create({'inventory_id': self.id, 'tracking_line_ids': wiz_lines})
            return {
                    'name': _('Tracked Products in Inventory Adjustment'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'stock.track.confirmation',
                    'target': 'new',
                    'res_id': wiz.id,
                }
        else:
            self._action_done()

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# PLM approval

# class mrp_eco_inherit(models.Model):
#     _inherit = "mrp.eco"

#     state = fields.Selection([
#         ('approve','To Approve'),
#         ('confirmed', 'To Do'),
#         ('progress', 'In Progress'),
#         ('rebase', 'Rebase'),
#         ('conflict', 'Conflict'),
#         ('done', 'Done')], string='Status',
#         copy=False, default='confirmed', readonly=True, required=True)

#     @api.multi
#     def action_new_revision(self):
#         return self.write({'state': 'approve'})

#     @api.multi
#     def button_approve(self, force=False):
#         IrAttachment = self.env['ir.attachment']  # FORWARDPORT UP TO SAAS-15
#         for eco in self:
#             if eco.type in ('bom', 'both'):
#                 eco.new_bom_id = eco.bom_id.copy(default={
#                     'version': eco.bom_id.version + 1,
#                     'active': False,
#                     'previous_bom_id': eco.bom_id.id,
#                 })
#                 attachments = IrAttachment.search([('res_model', '=', 'mrp.bom'),
#                                                    ('res_id', '=', eco.bom_id.id)])
#                 for attachment in attachments:
#                     attachment.copy(default={'res_id':eco.new_bom_id.id})
#             if eco.type in ('routing', 'both'):
#                 eco.new_routing_id = eco.routing_id.copy(default={
#                     'version': eco.routing_id.version + 1,
#                     'active': False,
#                     'previous_routing_id': eco.routing_id.id
#                 }).id
#                 attachments = IrAttachment.search([('res_model', '=', 'mrp.routing'),
#                                                    ('res_id', '=', eco.routing_id.id)])
#                 for attachment in attachments:
#                     attachment.copy(default={'res_id':eco.new_routing_id.id})
#             if eco.type == 'both':
#                 eco.new_bom_id.routing_id = eco.new_routing_id.id
#                 for line in eco.new_bom_id.bom_line_ids:
#                     line.operation_id = eco.new_routing_id.operation_ids.filtered(lambda x: x.name == line.operation_id.name).id
#             # duplicate all attachment on the product
#             if eco.type in ('bom', 'both', 'product'):
#                 attachments = self.env['mrp.document'].search([('res_model', '=', 'product.template'), ('res_id', '=', eco.product_tmpl_id.id)])
#                 for attach in attachments:
#                     attach.copy({'res_model': 'mrp.eco', 'res_id': eco.id})
#         # super(mrp_eco_inherit, self).write({'stage_id':'1'})
#         self.write({'state': 'progress'})

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# Manufacture approval

class mrp_unbuild_inherit(models.Model):
    _inherit = "mrp.unbuild"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve','To Approve'),
        ('done', 'Done')], string='Status', default='draft', index=True)

    @api.multi
    def action_validate(self):
        return self.write({'state': 'approve'})

    @api.multi
    def button_approve(self, force=False):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        available_qty = self.env['stock.quant']._get_available_quantity(self.product_id, self.location_id, self.lot_id, strict=True)
        if float_compare(available_qty, self.product_qty, precision_digits=precision) >= 0:
            return self.action_unbuild()
        else:
            return {
                'name': _('Insufficient Quantity'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.warn.insufficient.qty.unbuild',
                'view_id': self.env.ref('mrp.stock_warn_insufficient_qty_unbuild_form_view').id,
                'type': 'ir.actions.act_window',
                'context': {
                    'default_product_id': self.product_id.id,
                    'default_location_id': self.location_id.id,
                    'default_unbuild_id': self.id
                },
                'target': 'new'
            }

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# Manufacture approval

class mrp_routing_inherit(models.Model):
    _inherit = "mrp.routing"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve','To Approve'),
        ('done', 'Approved')], string='Status', default='draft', index=True)

    @api.multi
    def action_validate(self):
        return self.write({'state': 'approve'})

    @api.multi
    def button_approve(self, force=False):
        return self.write({'state': 'done'})



class maintenance_request_inherit(models.Model):
    _inherit = "maintenance.request"

    order_cus_ids = fields.Many2one('sale.order',string='Sale Order')
    project_loc = fields.Many2one('project.location',string='Project Name')
    customer_name = fields.Many2one('res.partner',string='Customer Name',related='order_cus_ids.partner_id',readonly=True,store=True)
    product_name = fields.Many2one('product.product',string='Product Name',readonly=True,compute="_product_name")
    product_serial = fields.Many2one('stock.production.lot',string='Serial No',readonly=True,compute="_product_serial")

    @api.onchange('order_cus_ids')
    def _product_name(self):
        for rec in self:
            for l in rec.order_cus_ids.order_line:
                if self.env['mrp.bom'].search([('product_tmpl_id','=',l.product_id.default_code)]):
                    rec.product_name = l.product_id
                else:
                    continue

    @api.onchange('production_id')
    def _product_serial(self):
        for rec in self:
            if rec.production_id.finished_move_line_ids:
                for l in rec.production_id.finished_move_line_ids:
                    if rec.production_id.product_id == l.product_id:
                        rec.product_serial = l.lot_id


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$44
# Packages line model

class package_line(models.Model):
    _name = "package.line"

    package_id = fields.Char('Package #',invisible=True)
    name = fields.Char('Package #',required=True)
    name_arabic = fields.Char('Package Name Arabic')
    package_dim = fields.Char('Dimension')
    package_gross = fields.Float('Gross Wgt.')
    Package_detail = fields.One2many('package.line.inh','package_ids',string='Package Details')

    @api.depends('name')
    def _name_sale(self):
        self.Package_detail.package_ids = self.name



class package_line_inh(models.Model):
    _name = "package.line.inh"

    # package_id = fields.Char('Package #',invisible=True)
    package_ids = fields.Many2one('package.line','Package #')
    package_des = fields.Text('Description')
    package_des_arabic = fields.Text('Description Arabic')
    package_qty = fields.Integer('Qty')
    package_net = fields.Float('Net Wgt.')

class product_line(models.Model):
    _name = "product.line"

    product_id = fields.Many2one('stock.picking','Id')
    product = fields.Char('Product #')
    qty = fields.Char('QTY')
    status = fields.Char('Status')
    types = fields.Char('Type')
    no = fields.Char('Serial number.')
    price = fields.Float('Cost')
    bom = fields.Integer('BOM')

class product2_line(models.Model):
    _name = "product2.line"

    product_id = fields.Many2one('stock.picking','Id')
    product = fields.Char('Product #')
    qty = fields.Char('QTY')
    status = fields.Char('Status')
    types = fields.Char('Type')
    no = fields.Char('Serial number.')
    price = fields.Float('Cost')
    bom = fields.Integer('BOM')

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$44
# Product line model

class project_location(models.Model):
    _name = "project.location"

    name = fields.Char('Project Name',required=True)

# ?????????????????????????????????????????????????????????????????????????????
# account invoice edit
class account_invoice_inherit(models.Model):
    _inherit = "account.invoice"

    text = fields.Char('Price in Text',compute="_com_price2",invisible=True)
    entire = fields.Char('Price in Text',compute="_com_price")
    decimal = fields.Char('Price in Text',compute="_com_price")
    text_tax = fields.Char('Price in Text',compute="_com_price2",invisible=True)
    entire_tax = fields.Char('Price in Text',compute="_com_price")
    decimal_tax = fields.Char('Price in Text',compute="_com_price")
    curr_change_untaxed = fields.Float('Untaxed Amount in AED',compute='_amount_change')
    curr_change_total = fields.Float('Total Amount in AED',compute='_amount_change')

    @api.multi
    def _amount_change(self):
        for rec in self:
            currency = rec.currency_id
            rec.curr_change_total = currency._convert(rec.amount_total, self.env.user.company_id.currency_id, self.env.user.company_id, date.today())
            rec.curr_change_untaxed = currency._convert(rec.amount_untaxed, self.env.user.company_id.currency_id, self.env.user.company_id, date.today())
            


    @api.depends('amount_total','currency_id')
    def _com_price2(self):
        # res = super(pur_order_inherit, self)._onchange_amount()
        self.text = self.currency_id.amount_to_text(self.amount_untaxed) if self.currency_id else ''
        self.text = self.text.replace(' And ', ' ').replace(',',' ')
        #self.text = self.text.replace(' Dirham ', ' ')

        self.text_tax = self.currency_id.amount_to_text(self.amount_tax) if self.currency_id else ''
        self.text_tax = self.text_tax.replace(' And ', ' ').replace(',',' ')
        #self.text_tax = self.text_tax.replace(' Dirham ', ' ')

    @api.multi
    def _com_price(self):
        # self.text = num2words(self.amount_total, lang='en')
        pre = float(self.amount_total)
        text1 = ''
        entire_num = int((str(pre).split('.'))[0])
        decimal_num = int((str(pre).split('.'))[1])
        if decimal_num < 10:
            decimal_num = decimal_num * 10        
        text1+=num2words(entire_num, lang='en')
        self.entire = num2words(entire_num, lang='en')
        self.entire = self.entire.replace(' and ', ' ')
        text1+=' and '
        text1+=num2words(decimal_num, lang='en')
        self.decimal = num2words(decimal_num, lang='en')
        #self.text = text1

        pre2 = float(self.amount_tax)
        text2 = ''
        entire_num2 = int((str(pre2).split('.'))[0])
        decimal_num2 = int((str(pre2).split('.'))[1])
        if decimal_num2 < 10:
            decimal_num2 = decimal_num2 * 10        
        text2+=num2words(entire_num2, lang='en')
        self.entire_tax = num2words(entire_num2, lang='en')
        self.entire_tax = self.entire_tax.replace(' and ', ' ')
        text2+=' and '
        text2+=num2words(decimal_num2, lang='en')
        self.decimal_tax = num2words(decimal_num2, lang='en')
        #self.text_tax = text2



# by Fouad For comparsion report 
# -------------------------------------------------------------------------------
# product supplier edit
class product_supplier_inherit(models.Model):
    _inherit = "product.supplierinfo"


    payment_terms = fields.Char('Payment Terms')
    warranty = fields.Char('Warranty')
    delivery_terms = fields.Char('Delivery Terms')

class StockProductionLot_inherit(models.Model):
    _inherit = "stock.production.lot"


    # @api.model_create_multi
    @api.model
    def create(self, vals):
        res = super(StockProductionLot_inherit, self).create(vals)
        com = self.env['stock.production.lot'].search([('name','=',vals.get('name'))])
        if com:
            raise UserError('The combination of serial number must be unique !')
        return res

    # _sql_constraints = [
    #     ('name_uniq', 'unique (name)', 'The combination of serial number must be unique !'),
    #     ('name_ref_uniq', 'unique ()', 'The combination of serial number and product must be unique !'),
    # ]

class StockQuantityHistoryinh(models.TransientModel):
    _inherit = 'stock.quantity.history'

    def open_table(self):
        if not self.env.context.get('valuation'):
            return super(StockQuantityHistoryinh, self).open_table()

        self.env['stock.move']._run_fifo_vacuum()

        if self.compute_at_date:
            tree_view_id = self.env.ref('stock_account.view_stock_product_tree2').id
            pivot_view_id = self.env.ref('wf_updates.view_stock_product_pivot2').id
            form_view_id = self.env.ref('stock.product_form_view_procurement_button').id
            search_view_id = self.env.ref('stock_account.view_inventory_valuation_search').id
            # We pass `to_date` in the context so that `qty_available` will be computed across
            # moves until date.
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form'), (pivot_view_id, 'pivot')],
                'view_mode': 'tree,form,pivot',
                'name': _('Inventory Valuation'),
                'res_model': 'product.product',
                'domain': "[('type', '=', 'product'), ('qty_available', '!=', 0)]",
                'context': dict(self.env.context, to_date=self.date, company_owned=True, create=False, edit=False),
                'search_view_id': search_view_id
            }
            return action
        else:
            return self.env.ref('stock_account.product_valuation_action').read()[0]

class Partner(models.Model):
    _inherit = "res.partner"

    vendor_name_arrrab = fields.Text('Vendor Name in arabic')

class productproductinh(models.Model):
    _inherit = "product.product"

    # stock_value_num = fields.Float('Stock Value')
    stock_value2 = fields.Float('Stock Value Amount')


    @api.multi
    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.remaining_value', 'product_tmpl_id.cost_method', 'product_tmpl_id.standard_price', 'product_tmpl_id.property_valuation', 'product_tmpl_id.categ_id.property_valuation')
    def _compute_stock_value(self):
        StockMove = self.env['stock.move']
        to_date = self.env.context.get('to_date')

        real_time_product_ids = [product.id for product in self if product.product_tmpl_id.valuation == 'real_time']
        if real_time_product_ids:
            self.env['account.move.line'].check_access_rights('read')
            fifo_automated_values = {}
            query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                         FROM account_move_line AS aml
                        WHERE aml.product_id IN %%s AND aml.company_id=%%s %s
                     GROUP BY aml.product_id, aml.account_id"""
            params = (tuple(real_time_product_ids), self.env.user.company_id.id)
            if to_date:
                query = query % ('AND aml.date <= %s',)
                params = params + (to_date,)
            else:
                query = query % ('',)
            self.env.cr.execute(query, params=params)

            res = self.env.cr.fetchall()
            for row in res:
                fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))

        product_values = {product.id: 0 for product in self}
        product_move_ids = {product.id: [] for product in self}

        if to_date:
            domain = [('product_id', 'in', self.ids), ('date', '<=', to_date)] + StockMove._get_all_base_domain()
            value_field_name = 'value'
        else:
            domain = [('product_id', 'in', self.ids)] + StockMove._get_all_base_domain()
            value_field_name = 'remaining_value'

        StockMove.check_access_rights('read')
        query = StockMove._where_calc(domain)
        StockMove._apply_ir_rules(query, 'read')
        from_clause, where_clause, params = query.get_sql()
        query_str = """
            SELECT stock_move.product_id, SUM(COALESCE(stock_move.{}, 0.0)), ARRAY_AGG(stock_move.id)
            FROM {}
            WHERE {}
            GROUP BY stock_move.product_id
        """.format(value_field_name, from_clause, where_clause)
        self.env.cr.execute(query_str, params)
        for product_id, value, move_ids in self.env.cr.fetchall():
            product_values[product_id] = value
            product_move_ids[product_id] = move_ids

        for product in self:
            if product.cost_method in ['standard', 'average']:
                qty_available = product.with_context(company_owned=True, owner_id=False).qty_available
                price_used = product.standard_price
                if to_date:
                    price_used = product.get_history_price(
                        self.env.user.company_id.id,
                        date=to_date,
                    )
                product.stock_value = price_used * qty_available
                product.qty_at_date = qty_available
            elif product.cost_method == 'fifo':
                if to_date:
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_value = product_values[product.id]
                        product.qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
                        product.stock_fifo_manual_move_ids = StockMove.browse(product_move_ids[product.id])
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (0, 0, [])
                        product.stock_value = value
                        product.qty_at_date = quantity
                        product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)
                else:
                    product.stock_value = product_values[product.id]
                    product.qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_fifo_manual_move_ids = StockMove.browse(product_move_ids[product.id])
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (0, 0, [])
                        product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)

        for rec in self:
            rec.write({'stock_value2':rec.stock_value})


class SaleOrderOptioninh(models.Model):
    _inherit = "sale.order.option"


    bom_nam = fields.Char('BOM Name appears in Quotation')
    num = fields.Integer('no')
    check = fields.Integer('check')
    bom_ok = fields.Binary('Is BOM',compute="_compute_bom")
    flow = fields.Float('Flow',compute="_compute_bom")
    flow_uom_id = fields.Many2one('uom.uom',compute="_compute_bom")
    head = fields.Char('Head',compute="_compute_bom")
    Pro_type = fields.Char('Product Type',compute="_compute_bom")
    Pro_type_dr = fields.Char('Product Type',compute="_compute_bom")
    Pro_type_con = fields.Char('Product Type',compute="_compute_bom")
    Type = fields.Char('Type',compute="_compute_bom")
    Type_dr = fields.Char('Type',compute="_compute_bom")
    Type_con = fields.Char('Type',compute="_compute_bom")
    manu = fields.Char('Manufacture',compute="_compute_bom")
    manu_dr = fields.Char('Manufacture',compute="_compute_bom")
    manu_con = fields.Char('Manufacture',compute="_compute_bom")
    model = fields.Char('Model',compute="_compute_bom")
    model_dr = fields.Char('Model',compute="_compute_bom")
    listing = fields.Char('Listing',compute="_compute_bom")
    listing_dr = fields.Char('Listing',compute="_compute_bom")
    listing_con = fields.Char('Listing',compute="_compute_bom")
    con = fields.Char('Construction',compute="_compute_bom")
    supply_dr = fields.Char('Supply',compute="_compute_bom")
    supply_con = fields.Char('Supply',compute="_compute_bom")
    enc_dr = fields.Char('Enclosure',compute="_compute_bom")
    enc_con = fields.Char('Enclosure',compute="_compute_bom")
    frame = fields.Char('Frame Size',compute="_compute_bom")
    acc = fields.Char('Accessories',compute="_compute_bom")
    speed = fields.Float('Speed',compute="_compute_bom")
    speed_uom_id = fields.Many2one('uom.uom',compute="_compute_bom")
    speed_dr = fields.Float('Speed',compute="_compute_bom")
    speed_uom_id_dr = fields.Many2one('uom.uom',compute="_compute_bom")
    rate_dr = fields.Float('Rating',compute="_compute_bom")
    rate_uom_id_dr = fields.Many2one('uom.uom',compute="_compute_bom")
    rate_con = fields.Float('Rating',compute="_compute_bom")
    rate_uom_id_con = fields.Many2one('uom.uom',compute="_compute_bom")
    #by fouad 

    no_of_stages = fields.Char('No Of Stages',compute="_compute_bom")
    Pro_type_ger = fields.Char('Gear Product Type',compute="_compute_bom")
    Type_ger = fields.Char('Gear Type',compute="_compute_bom")
    manu_gear = fields.Char('Gear Manufacture',compute="_compute_bom") 
    model_gear = fields.Char('Gear Model',compute="_compute_bom")
    ratio_gear = fields.Char('Gear Ratio',compute="_compute_bom")
    approval_gear = fields.Char('Gear Approval',compute="_compute_bom")

    # new changes ziad

    material_spec = fields.Char("Add'l Material Spec",compute="_compute_bom")
    spare_part = fields.Char("Spare Parts",compute="_compute_bom")
    # pump
    # driver
    fuel_tank = fields.Char("Fuel Tank Capacity",compute="_compute_bom")
    prv = fields.Char("PRV",compute="_compute_bom")
    silencer_type = fields.Char("Silencer Type",compute="_compute_bom")
    derating = fields.Char("Derating",compute="_compute_bom")
    # driver
    
    # Controller
    site_voltage = fields.Char("Site Voltage",compute="_compute_bom")
    charger_voltage = fields.Char("Charger Voltage",compute="_compute_bom")
    with_ats = fields.Char("With ATS",compute="_compute_bom")
    special_options = fields.Char("Special Options",compute="_compute_bom")
    # Controller
    # gear driver
    watertank = fields.Char("Watertank Depth",compute="_compute_bom")
    # gear driver
    # special options
    pressuge_gauge = fields.Selection(string='Pressuge Gauge', selection=[
        ('stand','Standard'),
        ('liqu','Liquired Filled')],compute="_compute_bom")
    waste_cone = fields.Char("Waste Cone",compute="_compute_bom")
    flame_arrester = fields.Char("Flame Arrester",compute="_compute_bom")
    remote_alarm = fields.Char("Remote Alarm",compute="_compute_bom")

    # new changes ziad

    @api.multi
    def _compute_bom(self):
        for rec in self:
            coz = self.env['mrp.bom'].search([('product_tmpl_id','=',rec.product_id.code)])
            if coz:
                rec.bom_nam = coz.bom_nam
            else:
                continue
                com = self.env['product.template'].search([('default_code','=',rec.product_id.code)])
                for l in com:
                    rec.flow = l.flow
                    rec.flow_uom_id = l.flow_uom_id.id
                    rec.head = l.head
                    rec.Type = l.Type
                    rec.Type_dr = l.Type_dr
                    rec.Type_con = l.Type_con
                    rec.manu = l.manu
                    rec.manu_dr = l.manu_dr
                    rec.manu_con = l.manu_con
                    rec.model = l.model
                    rec.model_dr = l.model_dr
                    rec.listing = l.listing
                    rec.listing_dr = l.listing_dr
                    rec.listing_con = l.listing_con
                    rec.con = l.con
                    rec.supply_dr = l.supply_dr
                    rec.supply_con = l.supply_con
                    rec.enc_dr = l.enc_dr
                    rec.enc_con = l.enc_con
                    rec.frame = l.frame
                    rec.acc = l.acc
                    rec.speed = l.speed
                    rec.speed_uom_id = l.speed_uom_id.id
                    rec.speed_dr = l.speed_dr
                    rec.speed_uom_id_dr = l.speed_uom_id_dr.id
                    rec.bom_ok = l.bom_ok 
                    rec.rate_dr = l.rate_dr
                    rec.rate_uom_id_dr = l.rate_uom_id_dr.id
                    rec.rate_con = l.rate_con
                    rec.rate_uom_id_con = l.rate_uom_id_con.id
                    rec.Pro_type = l.Pro_type
                    rec.Pro_type_dr = l.Pro_type_dr
                    rec.Pro_type_con = l.Pro_type_con
                    rec.Pro_type_ger = l.Pro_type_ger
                    rec.Type_ger  = l.Type_ger
                    rec.manu_gear = l.manu_gear
                    rec.model_gear = l.model_gear
                    rec.ratio_gear = l.ratio_gear
                    rec.approval_gear = l.approval_gear
                    rec.no_of_stages = l.no_of_stages
                    rec.material_spec = l.material_spec
                    rec.spare_part = l.spare_part
                    rec.site_voltage = l.site_voltage
                    rec.with_ats = l.with_ats
                    rec.special_options = l.special_options
                    rec.watertank = l.watertank
                    rec.pressuge_gauge = l.pressuge_gauge
                    rec.waste_cone = l.waste_cone
                    rec.flame_arrester = l.flame_arrester
                    rec.remote_alarm = l.remote_alarm
                    rec.charger_voltage = l.charger_voltage
                    rec.silencer_type = l.silencer_type
                    rec.prv = l.prv
                    rec.fuel_tank = l.fuel_tank
                    rec.derating = l.derating


class accountmoveinheirt3(models.Model):
    _inherit = 'account.payment'

    prepare = fields.Char('Prepared by')
    checked = fields.Char('Checked by')
    received = fields.Char('Received by')
    approved = fields.Char('Approved by')
    verified = fields.Char('Verified by')