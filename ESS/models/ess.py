# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools ,_
from odoo.exceptions import  ValidationError,UserError
from odoo.exceptions import AccessError, UserError, RedirectWarning,Warning
import datetime 
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import odoo.exceptions
import re 

class employee_service(models.Model):
    _name = 'prepayment.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")
    emp_name = fields.Many2one('res.users',string='Employee Name',readonly=True,default=lambda self: self.env.uid)
    Ben_name = fields.Char('Beneficiary Name',required=True,track_visibility="onchange")
    emp_bank_num = fields.Char(string="Beneficiary Account Number",required=True,track_visibility="onchange")
    emp_man = fields.Char('Employee Manager',compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager',compute="_get_manager")
    test = fields.Boolean('Test',compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    emp_man_user = fields.Many2one('res.users',compute="_get_manager")
    bank_name = fields.Many2one('res.bank',string='Bank Name',required=True,track_visibility="onchange")
    currency = fields.Many2one('res.currency',string='Payment Currency',required=True,track_visibility="onchange")
    amount = fields.Float('Amount',required=True,track_visibility="onchange")
    inv_num = fields.Char('Invoice No',required=True,track_visibility="onchange")
    inv_date = fields.Date('Invoice Date', required=True, track_visibility="onchange")
    pay_due_date = fields.Date('Payment Due Date',required=True, track_visibility="onchange")
    Description = fields.Text('Description',required=True, track_visibility="onchange")
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')


    action_to_do = fields.Selection([('a', 'Not Excuted '),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")

    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")

    # @api.constrains('emp_bank_num')
    # def _iban_check_digits(self):
    #     for rec in self:
    #         iban_number = rec.emp_bank_num
    #         if iban_number[0].isupper() and iban_number[1].isupper():
    #             if len(iban_number) == 25:
    #                 continue
    #             else:
    #                 raise ValidationError(_("Please Enter A Valid IBAN Number Between The Formula Like: AE460090000000123456789"))
    #         else:
    #             raise ValidationError(_("First two Letters should be UPPERCASE"))
            
          



    @api.constrains('pay_due_date')
    def check_pay_due_date(self):
        for rec in self:
            if rec.pay_due_date < datetime.date.today():
                raise ValidationError(_("Payment Due Date Not Be Past Date"))
    

    @api.constrains('inv_date')
    def check_inv_date(self):
        for rec in self:
            if rec.inv_date > datetime.date.today():
                raise ValidationError(_("Invoice Date Should Not Be Future Date"))

    @api.multi
    @api.depends('Ben_name')
    def _com_today(self):
        for rec in self:
            rec.Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)


    @api.multi
    def _get_manager(self):
        for rec in self:
            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.test2 = False


            com = self.env['hr.employee'].search([('user_id','=',rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id','=',rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid :
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        

    # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id','=',rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.prepayment_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 


    # by fouad 
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})

    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})

    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('prepayment.request') or 'New'   

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Prepayment Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service, self).create(vals)       

        return result


    

# permanent window------------------------------------
class employee_service_permanent(models.Model):
    _name = 'permanent.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    Ben_name = fields.Char('Beneficiary Name', required=True, track_visibility="onchange")
    amount = fields.Float('Amount',required=True,track_visibility="onchange")
    Description = fields.Text('Description',required=True)
    emp_name = fields.Many2one('res.users',string='Employee Name',readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager',compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)

    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')



    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")

    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")

    @api.multi
    @api.depends('Ben_name')
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)



    @api.multi
    def _get_manager(self):
        for rec in self:
            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False

            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.permanent_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})

    
    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})

    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('permanent.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Permanent Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_permanent, self).create(vals)

        return result


# Credit/Debit window------------------------------------
class employee_service_credit_debit(models.Model):
    _name = 'credit.debit.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    Ben_name = fields.Char('Beneficiary Name', required=True, track_visibility="onchange")
    inv_num = fields.Char('Original Invoice No', required=True, track_visibility="onchange")
    inv_date = fields.Date('Original Invoice Date', required=True, track_visibility="onchange")
    org_amount = fields.Float('Original Invoice Amount', required=True, track_visibility="onchange")
    amount = fields.Float('Amount', required=True, track_visibility="onchange")
    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")
    Description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")

    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")
    @api.multi
    @api.depends('Ben_name')
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)


    @api.constrains('inv_date')
    def _check_inv_date(self):
        for rec in self:
            if rec.inv_date > datetime.date.today():
                raise ValidationError(_("Invoice Date Should Not Be Future Date"))


    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False

            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.credit_debit_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})

    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})

    
    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('credit.debit.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Credit Debit Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_credit_debit, self).create(vals)

        return result




# Temporary Petty Cash Payment  window------------------------------------

class employee_service_temporary_Petty(models.Model):
    _name = 'temporary.petty.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    Ben_name = fields.Char('Beneficiary Name', required=True, track_visibility="onchange")
    amount = fields.Float('Amount(AED)', required=True, track_visibility="onchange")
    Description = fields.Text('Description', required=True)
    sett_due_date = fields.Date('Settlement Due Date', required=True, track_visibility="onchange")
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')


    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")


    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")
    @api.multi
    @api.depends('Ben_name')
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.constrains('sett_due_date')
    def check_pay_due_date(self):
        for rec in self:
            if rec.sett_due_date < datetime.date.today():
                raise ValidationError(_("Payment Due Date Not Be Past Date"))

    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False

            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.temporary_petty_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})

    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})

    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('credit.debit.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Temporary Petty Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_temporary_Petty, self).create(vals)

        return result



# Invoices Payment Request window------------------------------------

class employee_service_invoices_payment(models.Model):
    _name = 'invoices.payment.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    Ben_name = fields.Char('Beneficiary Name', required=True, track_visibility="onchange")
    Ben_bank_num = fields.Char('Beneficiary Account Number', required=True, track_visibility="onchange")
    contract_num = fields.Char('Contract /PO NO.', required=True, track_visibility="onchange")
    num_of_rec = fields.Char('Number of receipt Stores/certificate of completion of the work', required=True,
                             track_visibility="onchange")
    bank_name = fields.Many2one('res.bank', string='Beneficiary Bank Name', required=True, track_visibility="onchange")
    currency = fields.Many2one('res.currency', string='Payment Currency', required=True, track_visibility="onchange")
    amount = fields.Float('Amount', required=True, track_visibility="onchange")
    inv_num = fields.Char('Invoice No', required=True, track_visibility="onchange")
    inv_date = fields.Date('Invoice Date', required=True, track_visibility="onchange")
    Payment_Du_Date = fields.Date('Payment Due Date', required=True, track_visibility="onchange")
    Description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')



    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")

    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")
    @api.multi
    @api.depends('Ben_name')
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    # @api.constrains('Ben_bank_num')
    # def _iban_check_digits(self):
    #     for rec in self:
    #         iban_number = rec.Ben_bank_num
    #         if iban_number[0].isupper() and iban_number[1].isupper():
    #             if len(iban_number) == 25:
    #                 continue
    #             else:
    #                 raise ValidationError(_("Please Enter A Valid IBAN Number Between The Formula Like: AE460090000000123456789"))
    #         else:
    #             raise ValidationError(_("First two Letters should be UPPERCASE"))


    @api.constrains('inv_date')
    def _check_inv_date(self):
        for rec in self:
            if rec.inv_date > datetime.date.today():
                raise ValidationError(_("Invoice Date Should Not Be Future Date"))


    @api.constrains('Payment_Du_Date')
    def check_pay_due_date(self):
        for rec in self:
            if rec.Payment_Du_Date < datetime.date.today():
                raise ValidationError(_("Payment Due Date Not Be Past Date"))

    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.invoices_payment_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})

    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})

    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('invoices.payment.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Invoices Payment Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_invoices_payment, self).create(vals)

        return result


#  Petty Cash Payment  window------------------------------------

class employee_service_Petty_cash(models.Model):
    _name = 'petty.cash.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    Ben_name = fields.Char('Beneficiary Name', required=True, track_visibility="onchange")
    amount = fields.Float('Amount(AED)', required=True, track_visibility="onchange")
    inv_num = fields.Char('Batch/Invoice No', required=True, track_visibility="onchange")
    inv_date = fields.Date('Batch/Invoice Date', required=True, track_visibility="onchange")
    Description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')

    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")

    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")

    @api.multi
    @api.depends('Ben_name')
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    
    @api.constrains('inv_date')
    def _check_inv_date(self):
        for rec in self:
            if rec.inv_date > datetime.date.today():
                raise ValidationError(_("Invoice Date Should Not Be Future Date"))

    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.petty_cash_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})


    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})

    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('petty.cash.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Petty Cash Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_Petty_cash, self).create(vals)

        return result





#  Human Resources Payment  window------------------------------------

class employee_service_human_resources(models.Model):
    _name = 'human.resources.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    depart = fields.Many2one('hr.department', string='Department')
    be_acc_num_one = fields.Char('Batch/Beneficiary Bank Account Number', required=True, track_visibility="onchange")
    bat_ben_name = fields.Char('Batch/Beneficiary Name', required=True, track_visibility="onchange")
    be_acc_num_two = fields.Char('Batch/Beneficiary Bank Account Number', required=True, track_visibility="onchange")
    amount = fields.Float('Total Amount', required=True, track_visibility="onchange")
    choos_one = fields.Many2one('res.users', string='choose from list')
    choos_two = fields.Many2one('res.users', string='choose from list')
    choos_three = fields.Many2one('res.users', string='choose from list')
    choos_four = fields.Many2one('res.users', string='choose from list')
    accruals = fields.Char('Accruals', required=True, track_visibility="onchange")
    Description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')


    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")


    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")
    @api.multi
    @api.depends('bat_ben_name')
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    # @api.constrains('be_acc_num_one')
    # def _iban_check_digits(self):
    #     for rec in self:
    #         iban_number = rec.be_acc_num_one
    #         x = re.findall("^[0-9]",iban_number,2)
    #         if (x):
    #             raise ValidationError(_("Please Enter A Valid IBAN Number Between The Formula Lilk: AE460090000000123456789"))
   
    # @api.constrains('be_acc_num_two')
    # def _iban_check_digits(self):
    #     for rec in self:
    #         iban_number = rec.be_acc_num_two
    #         if iban_number[0].isupper() and iban_number[1].isupper():
    #             if len(iban_number) == 25:
    #                 continue
    #             else:
    #                 raise ValidationError(_("Please Enter A Valid IBAN Number Between The Formula Like: AE460090000000123456789"))
    #         else:
    #             raise ValidationError(_("First two Letters should be UPPERCASE"))
    
    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.human_resources_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})


    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})

    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('human.resources.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Human Resources Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_human_resources, self).create(vals)

        return result





#  LC BG Payment  window------------------------------------

class employee_service_lc_bg(models.Model):
    _name = 'lc.bg.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    type = fields.Selection([('a', 'Statut A'),('b', 'Statut B')])
    Ben_name = fields.Char('Beneficiary Name', required=True, track_visibility="onchange")
    contract_num = fields.Char('Contract No', required=True, track_visibility="onchange")
    currency = fields.Many2one('res.currency', string='Payment Currency', required=True,
                               track_visibility="onchange")
    amount = fields.Float('Amount(AED)', required=True, track_visibility="onchange")
    period_one = fields.Date('Period From', required=True, track_visibility="onchange")
    period_two = fields.Date('Period To', required=True, track_visibility="onchange")
    Description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')

    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")


    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")

    @api.multi
    @api.depends('Ben_name')
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions

    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.lc_bg_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 

    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})

    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})

    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('lc.bg.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'LC BG Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_lc_bg, self).create(vals)

        return result



#  Prepayment  Settlement  window------------------------------------

class employee_service_prepayment_settlement(models.Model):
    _name = 'prepayment.settlement.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    pre_num = fields.Char('Prepayment Request NO.', required=True, track_visibility="onchange")
    currency = fields.Many2one('res.currency',string='Prepayment Currency',required=True,track_visibility="onchange")
    amount = fields.Float('Prepayment Amount', required=True, track_visibility="onchange")
    tot_cost = fields.Float('Total Costs', required=True, track_visibility="onchange")
    despos_amo = fields.Float('Deposit Amount', required=True, track_visibility="onchange",compute="_check_deposit")
    surplus_amo = fields.Float('Surplus Amount', required=True, track_visibility="onchange",compute="_check_surplus")
    increas_of_prepa = fields.Float('% Increase of prepayment', required=True, track_visibility="onchange",compute="_check_increas")
    reasons_surplus = fields.Text('Reasons for Surplus', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')


    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")


    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")
    @api.multi
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.depends('amount','tot_cost')
    def _check_deposit(self):
        for rec in self:
            valu = (rec.amount - rec.tot_cost)
            if valu > 0:
                rec.despos_amo = valu

            else:
                rec.despos_amo = 0

    @api.depends('amount', 'tot_cost')
    def _check_surplus(self):
        for rec in self:
            valu = (rec.amount - rec.tot_cost)
            if valu < 0:
                rec.surplus_amo = (rec.tot_cost - rec.amount)
            else:
                rec.surplus_amo = 0

    @api.depends('surplus_amo', 'amount')
    def _check_increas(self):
        for rec in self:
            if rec.amount > 0:
                valu = (rec.surplus_amo/rec.amount)
                if valu <= 0.05:
                    rec.increas_of_prepa = valu
                else:
                    print("We can not complete the request due to Exceeded the permissible Percentage")



    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.prepayment_settlement_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})

    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})

    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('prepayment.settlement.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Prepayment Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_prepayment_settlement, self).create(vals)

        return result





#  prepayment Petty Cash Settlement Request Form------------------------------------

class employee_service_prepayment_petty_cash_settlement(models.Model):
    _name = 'prepayment.petty.cash.settlement.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    pre_num = fields.Char('prepayment Petty Cash Request NO. ', required=True, track_visibility="onchange")
    discerption = fields.Text('Description', required=True)
    amount = fields.Float('prepayment Petty Cash  Amount', required=True, track_visibility="onchange")
    tot_cost = fields.Float('Total Costs', required=True, track_visibility="onchange")
    despos_amo = fields.Float('Deposit Amount', required=True, track_visibility="onchange",compute="_check_deposit")
    surplus_amo = fields.Float('Surplus Amount', required=True, track_visibility="onchange",compute="_check_surplus")
    increas_of_prepa = fields.Float('% Increase of prepayment', required=True, track_visibility="onchange",compute="_check_increas")
    reasons_surplus = fields.Text('Reasons for Surplus', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')


    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")


    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")

    @api.multi
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.depends('amount', 'tot_cost')
    def _check_deposit(self):
        for rec in self:
            valu = (rec.amount - rec.tot_cost)
            if valu > 0:
                rec.despos_amo = valu

            else:
                rec.despos_amo = 0

    @api.depends('amount', 'tot_cost')
    def _check_surplus(self):
        for rec in self:
            valu = (rec.amount - rec.tot_cost)
            if valu <= 0:
                rec.surplus_amo = (rec.tot_cost - rec.amount)
            else:
                rec.surplus_amo = 0

    @api.depends('surplus_amo', 'amount')
    def _check_increas(self):
        for rec in self:
            if rec.amount > 0:
                valu = (rec.surplus_amo / rec.amount)
                if valu <= 0.05:
                    rec.increas_of_prepa = valu
                else:
                    print("We can not complete the request due to Exceeded the permissible Percentage")


    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.prepayment_petty_cash_settlement_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})

    
    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})

    
    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('prepayment.petty.cash.settlement.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Prepayment Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_prepayment_petty_cash_settlement, self).create(vals)

        return result




#  Temporary Petty Cash Settlement Request Form------------------------------------

class employee_service_temporary_petty_cash_settlement(models.Model):
    _name = 'temporary.petty.cash.settlement.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    pre_num = fields.Char('Temporary Petty Cash Request NO. ', required=True, track_visibility="onchange")
    discerption = fields.Text('Description', required=True)
    amount = fields.Float('Temporary Petty Cash  Amount', required=True, track_visibility="onchange")
    tot_cost = fields.Float('Total Costs', required=True, track_visibility="onchange")
    despos_amo = fields.Float('Deposit Amount', required=True, track_visibility="onchange",compute="_check_deposit")
    surplus_amo = fields.Float('Surplus Amount', required=True, track_visibility="onchange",compute="_check_surplus")
    increas_of_prepa = fields.Float('% Increase of prepayment', required=True, track_visibility="onchange",compute="_check_increas")
    reasons_surplus = fields.Text('Reasons for Surplus', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')


    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")

    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")
    @api.multi
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)


    @api.depends('amount', 'tot_cost')
    def _check_deposit(self):
        for rec in self:
            valu = (rec.amount - rec.tot_cost)
            if valu > 0:
                rec.despos_amo = valu

            else:
                rec.despos_amo = 0

    @api.depends('amount', 'tot_cost')
    def _check_surplus(self):
        for rec in self:
            valu = (rec.amount - rec.tot_cost)
            if valu <= 0:
                rec.surplus_amo = (rec.tot_cost - rec.amount)
            else:
                rec.surplus_amo = 0

    @api.depends('surplus_amo', 'amount')
    def _check_increas(self):
        for rec in self:
            if rec.amount > 0:
                valu = (rec.surplus_amo / rec.amount)
                if valu <= 0.05:
                    rec.increas_of_prepa = valu
                else:
                    print("We can not complete the request due to Exceeded the permissible Percentage")


    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.temporary_petty_cash_settlement_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})


    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})
   
    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('temporary.petty.cash.settlement.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Temporary Petty Cash Settlement Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_temporary_petty_cash_settlement, self).create(vals)

        return result



#  Permenant Petty Cash Reimbursement Request Form ------------------------------------

class employee_service_permenant_petty_cash_reimbursement(models.Model):
    _name = 'permenant.petty.cash.reimbursement.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    pre_num = fields.Char('Premenant Petty Cash Request NO.', required=True, track_visibility="onchange")
    amount = fields.Float('Temporary Petty Cash  Amount', required=True, track_visibility="onchange")
    tot_cost = fields.Float('Total Costs', required=True, track_visibility="onchange")
    reimbu_amo = fields.Float('Reimbursement Amount', required=True, track_visibility="onchange")
    discerption = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')


    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")

    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")

    @api.multi
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)


    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.permenant_petty_cash_reimbursement_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})

    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})
   
    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('permenant.petty.cash.reimbursement.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Permenant Petty Cash Reimbursement Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_permenant_petty_cash_reimbursement, self).create(vals)

        return result


#   Receipts Post Date Cheque Request window------------------------------------

class employee_service_receipts_post_date_cheque(models.Model):
    _name = 'receipts.post.date.cheque.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    customer_name = fields.Char('Customer Name', required=True, track_visibility="onchange")
    cheque_num = fields.Char('Cheque NO.', required=True, track_visibility="onchange")
    cheque_amo = fields.Float('Cheque Amount', required=True, track_visibility="onchange")
    due_date = fields.Date('Due Date', required=True, track_visibility="onchange")
    inv_num = fields.Char('Invoice NO.', required=True, track_visibility="onchange")
    inv_date = fields.Date('Invoice Date', required=True, track_visibility="onchange")
    inv_amo = fields.Float('Invoice Amount', required=True, track_visibility="onchange")
    Description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')


    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")



    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")
    @api.multi
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.constrains('due_date')
    def check_pay_due_date(self):
        for rec in self:
            if rec.due_date < datetime.date.today():
                raise ValidationError(_("Payment Due Date Not Be Past Date"))
    

    @api.constrains('inv_date')
    def check_inv_date(self):
        for rec in self:
            if rec.inv_date > datetime.date.today():
                raise ValidationError(_("Invoice Date Should Not Be Future Date"))


    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.receipts_post_date_cheque_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})


    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})
   
    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('employee_service_receipts_post_date_cheque') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Receipts Post Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_receipts_post_date_cheque, self).create(vals)

        return result




#    Receipts Current Date Cheque Request  window------------------------------------

class employee_service_receipts_current_date_cheque(models.Model):
    _name = 'receipts.current.date.cheque.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    customer_name = fields.Char('Customer Name', required=True, track_visibility="onchange")
    cheque_num = fields.Char('Cheque NO.', required=True, track_visibility="onchange")
    cheque_amo = fields.Float('Cheque Amount', required=True, track_visibility="onchange")
    inv_num = fields.Char('Invoice NO.', required=True, track_visibility="onchange")
    inv_date = fields.Date('Invoice Date', required=True, track_visibility="onchange")
    inv_amo = fields.Float('Invoice Amount', required=True, track_visibility="onchange")
    Description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')


    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")


    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")
    @api.multi
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.constrains('inv_date')
    def check_inv_date(self):
        for rec in self:
            if rec.inv_date > datetime.date.today():
                raise ValidationError(_("Invoice Date Should Not Be Future Date"))

    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.receipts_current_date_cheque_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})


    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})
   
    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('receipts.current.date.cheque.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Receipts Current Date Cheque Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_receipts_current_date_cheque, self).create(vals)

        return result



#    Receipts Cash Request window------------------------------------

class employee_service_receipts_cash(models.Model):
    _name = 'receipts.cash.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    customer_name = fields.Char('Customer Name', required=True, track_visibility="onchange")
    inv_num = fields.Char('Invoice NO.', required=True, track_visibility="onchange")
    inv_date = fields.Date('Invoice Date', required=True, track_visibility="onchange")
    inv_amo = fields.Float('Invoice Amount', required=True, track_visibility="onchange")
    Description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')


    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")

    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")
    @api.multi
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.constrains('inv_date')
    def check_inv_date(self):
        for rec in self:
            if rec.inv_date > datetime.date.today():
                raise ValidationError(_("Invoice Date Should Not Be Future Date"))

    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.receipts_cash_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})

    
    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})
   
    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('receipts.cash.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Receipts Cash Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_receipts_cash, self).create(vals)

        return result


#    Intercompany transaction Reques window------------------------------------

class employee_service_intercompany_transaction(models.Model):
    _name = 'intercompany.transaction.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    type = fields.Selection([('a', 'Statut A'),('b', 'Statut B')])
    trans_date = fields.Date('Transaction Date', required=True, track_visibility="onchange")
    trans_amo = fields.Float('Transaction Amount', required=True, track_visibility="onchange")
    currency = fields.Many2one('res.currency',string='Transaction Currency',required=True,track_visibility="onchange")
    Description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')



    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")

    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")
    @api.multi
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.intercompany_transaction_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})


    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})
   
    # Buttons actions
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('intercompany.transaction.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Intercompany Transaction Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_intercompany_transaction, self).create(vals)

        return result



#    Human Resources Accruals Request  window------------------------------------

class employee_service_human_resources_accruals(models.Model):
    _name = 'human.resources.accruals.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    ledger = fields.Selection([('a', 'Statut A'),('b', 'Statut B')])
    total_amo = fields.Float('Total Amount', required=True, track_visibility="onchange")
    basic_sal = fields.Float('Basic Salary', required=True, track_visibility="onchange")
    basic_sal_arre = fields.Float('Basic Salary Arrears', required=True, track_visibility="onchange")
    phone_all = fields.Float('Phone Allowances', required=True, track_visibility="onchange")
    over_time = fields.Char('Over Time', required=True, track_visibility="onchange" )
    car_all = fields.Float('Car Allowances', required=True, track_visibility="onchange" )
    phone_all_arre = fields.Float('Phone Allowances Arrears', required=True, track_visibility="onchange" )
    over_time_arre = fields.Float('Over Time  Arrears', required=True, track_visibility="onchange" )
    car_all_arr = fields.Float('Car Allowances Arrears', required=True, track_visibility="onchange" )
    fuel_all = fields.Float('Fuel Allowances', required=True, track_visibility="onchange" )
    other_all = fields.Float('Other Allowances', required=True, track_visibility="onchange" )
    other_all_arr = fields.Float('Other Allowances Arrears', required=True, track_visibility="onchange" )
    fuel_all_arr = fields.Float('Fuel Allowances  Arrears', required=True, track_visibility="onchange" )
    accom_all = fields.Float('Accommodation Allowance', required=True, track_visibility="onchange" )
    accom_all_arr = fields.Float('Accommodation Allowance Arrears', required=True, track_visibility="onchange" )
    advance_salary = fields.Float('Advance Salary', required=True, track_visibility="onchange")
    leave_salay = fields.Float('Leave Salary', required=True, track_visibility="onchange")
    leave_encash = fields.Float('Leave Encashment', required=True, track_visibility="onchange")
    leave_provi = fields.Float('Leave Provision', required=True, track_visibility="onchange")
    air_ticket_encash = fields.Float('Air Ticket Encashment', required=True, track_visibility="onchange")
    grat_enca = fields.Float('Gratuity Encashment (Regular)', required=True, track_visibility="onchange")
    air_ticket_provi = fields.Float('Air Ticket Provision', required=True, track_visibility="onchange")
    hour_leave_deduc = fields.Float('Hourly Leave Deduction', required=True, track_visibility="onchange")
    advance_salary_rec = fields.Float('Advance Salary Recovery', required=True, track_visibility="onchange")
    gratuity_provi = fields.Float('Gratuity Provision', required=True, track_visibility="onchange")
    unpaid_leave_dedu = fields.Float('Unpaid Leave Deduction', required=True, track_visibility="onchange")
    vechiles_other_dedu = fields.Float('Vechiles Other Deductions', required=True, track_visibility="onchange")
    vechiles_fines_dedu = fields.Float('Vechiles Fines Deductions', required=True, track_visibility="onchange")
    late_coming_dedu = fields.Float('Late Coming Deduction', required=True, track_visibility="onchange")
    Description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')


    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")

    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")
    @api.multi
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.human_resources_accruals_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})

    
    
    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})
   
    # Buttons actions human_resources_accruals_request_seq_name
    ##################################################

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('human.resources.Accruals.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Human Resources Accruals Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_human_resources_accruals, self).create(vals)

        return result



#    Preforma/Sales Invoice Request Form  window------------------------------------

class employee_service_preforma_sales_invoice(models.Model):
    _name = 'preforma.sales.invoice.request'
    _inherit = 'mail.thread'
    # _order = 'name desc'

    name = fields.Char('Reference No', required=True, copy=False, readonly=True, default='New')
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True,default=lambda self: self.env.uid)
    emp_man = fields.Char('Employee Manager', compute="_get_manager")
    emp_man_user = fields.Many2one('res.users', compute="_get_manager")
    emp_man_id = fields.Integer('Employee Manager', compute="_get_manager")
    test = fields.Boolean('Test', compute='_get_manager')
    test2 = fields.Boolean('Test2',compute='_get_manager',default=True)
    customer_name = fields.Char('Customer Name', required=True, track_visibility="onchange")
    Contract = fields.Char('Contract/PO/WO NO', required=True, track_visibility="onchange")
    inv_amount = fields.Float('Invoice Amount', required=True, track_visibility="onchange")
    due_date = fields.Date('Due Date', required=True, track_visibility="onchange")
    Description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Requested'),
        ('man', 'Requested Manager'),
        ('acc', 'Accounts'),
        ('cfo', 'Finance Manager'),
        ('teller','Archive'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')


    cre_Date = fields.Char('Date',compute="_com_today",track_visibility="onchange")

    action_to_do = fields.Selection([('a', 'Not Excuted'),('b', 'Excuted')],  copy=False, index=True, track_visibility='onchange', track_sequence=3, default='a')
    done_man =fields.Boolean('Approved By Requested Manager',default=False,track_visibility="onchange")
    done_acc =fields.Boolean('Approved By Accounts',default=False,track_visibility="onchange")
    done =fields.Boolean('Approved By CFO',default=False,track_visibility="onchange")
    man_rej = fields.Boolean('Rejectd By Requested Manager',default=False,track_visibility="onchange")
    rej_acc = fields.Boolean('Rejectd By Accounts',default=False,track_visibility="onchange")
    rej = fields.Boolean('Rejectd By CFO',default=False,track_visibility="onchange")


    con = fields.Boolean('Approv by',default=False,track_visibility="onchange")
    @api.multi
    def _com_today(self):
        for rec in self:
            rec.cre_Date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.constrains('due_date')
    def check_pay_due_date(self):
        for rec in self:
            if rec.due_date < datetime.date.today():
                raise ValidationError(_("Payment Due Date Not Be Past Date"))

    @api.multi
    def _get_manager(self):
        for rec in self:

            if rec.emp_name.id == rec.env.uid:
                rec.test2 = True
            else:
                rec.Test2 = False


            com = self.env['hr.employee'].search([('user_id', '=', rec.emp_name.id)])
            for l in com:
                rec.emp_man = l.parent_id.name
                rec.emp_man_id = l.parent_id.id
            cos = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in cos:
                rec.emp_man_user = l.user_id.id
                # raise UserError(_(rec.emp_man_user))
            if rec.emp_man_user.id == rec.env.uid:
                rec.test = True
                # raise UserError(_(rec.test))
            else:
                rec.test = False
                # raise UserError(_(rec.test))
        # raise UserError(_(rec.test))

        # Buttons actions
    @api.multi
    def action_confirm(self):
        email = ''
        for rec in self:
            com = self.env['hr.employee'].search([('id', '=', rec.emp_man_id)])
            for l in com:
                email = l.work_email
        template = self.env.ref('ESS.preforma_sales_invoice_request_email_template')
        template.write({'email_to': email})
        template.send_mail(self.ids[0], force_send=True)
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'Confirm Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'}) & self.write({'con': True})

    @api.multi
    def action_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_acc_return(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'Accountant return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})

    @api.multi
    def action_return_manager(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'Manager return the request to requester',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_return_acc(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Accountant',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'})

    @api.multi
    def action_return_man(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'CFO return the request to Manager',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'man'})

    @api.multi
    def action_man_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return  self.write({'state': 'teller'}) & self.write({'rej_acc': True}) 

    @api.multi
    def action_cfo_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'CFO Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'rej': True})

    @api.multi
    def action_manager_reject(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Reject',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'man_rej': True}) 

    @api.multi
    def action_man_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'Requester Manager Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done_man': True})

    @api.multi
    def action_acc_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'cfo'}) & self.write({'done_acc': True}) 

    @api.multi
    def action_cfo_approve(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'CFO Approve',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'acc'}) & self.write({'done': True}) 
    
    @api.multi
    def action_acc_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'b'})

    
    @api.multi
    def action_acc_not_excuted(self):
        log = self.env['test.logs.request']
        data = {
            'name': self.name,
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'Accountant Not Excuted',
            'date': datetime.datetime.today(),
        }
        log.create(data)
        return self.write({'state': 'teller'}) & self.write({'action_to_do': 'a'})
   
    # Buttons actions
    ################################################## 

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('pr.preforma.sales.invoice.Accruals.request') or 'New'

        vals['emp_name'] = self.env.uid
        log = self.env['test.logs.request']
        data = {
            'name': vals['name'],
            'screen_name': 'Preforma Sales Invoice Request',
            'emp_name': self.env.uid,
            'type': 'Create Request',
            'date': datetime.datetime.today(),
        }
        log.create(data)

        result = super(employee_service_preforma_sales_invoice, self).create(vals)

        return result



#    Preforma/Sales Invoice Request Form  window------------------------------------

class test_logs(models.Model):
    _name = 'test.logs.request'
    _inherit = 'mail.thread'
    _order = 'name desc'

    name = fields.Char('Reference No',readonly=True,required=True)
    emp_name = fields.Many2one('res.users', string='Employee Name', readonly=True)
    type = fields.Char('Type of Action', readonly=True)
    screen_name = fields.Char('Request Type', readonly=True)
    date = fields.Datetime('Date of action', readonly=True)



class dashbord_kanban(models.Model):
    _name = 'dash.bord.kanban.viwe'


    color = fields.Integer('Color')


    def _get_action(self, action_xmlid):
        # TDE TODO check to have one view + custo in methods
        action = self.env.ref(action_xmlid).read()[0]
  
        return action

    def get_action_prepayment_tree(self):
        return self._get_action('ESS.prepayment_request_menu_action')

    def get_action_permanent_tree_backorder(self):
        return self._get_action('ESS.permanent_request_menu_action')

    def get_action_credit_tree_waiting(self):
        return self._get_action('ESS.credit_debit_request_menu_action')

    def get_action_temporary_tree_ready(self):
        return self._get_action('ESS.temporary_petty_request_menu_action')

    def get_stock_invoices_action_picking_type(self):
        return self._get_action('ESS.invoices_payment_request_menu_action')

    def get_petty_cash_action_picking_type(self):
        return self._get_action('ESS.petty_cash_request_menu_action')

    def get_stock_human_resources_action_picking_type(self):
        return self._get_action('ESS.human_resources_request_menu_action')

    def get_lc_bg_action_picking_type(self):
        return self._get_action('ESS.lc_bg_request_menu_action')

    def get_prepayment_settlement_action_picking_type(self):
        return self._get_action('ESS.prepayment_settlement_request_menu_action')

    def get_prepayment_petty_action_picking_type(self):
        return self._get_action('ESS.prepayment_petty_cash_request_menu_action')

    def get_temporary_petty_cash_settlement_action_picking_type(self):
        return self._get_action('ESS.temporary_petty_cash_settlement_request_menu_action')

    def get_permenant_petty_cash_reimbursement_action_picking_type(self):
        return self._get_action('ESS.permenant_petty_cash_reimbursement_request_tree')

    def get_receipts_post_date_cheque_action_picking_type(self):
        return self._get_action('ESS.receipts_post_date_cheque_request_menu_action')

    def get_receipts_current_date_cheque_action_picking_type(self):
        return self._get_action('ESS.receipts_current_date_cheque_request_menu_action')

    def get_receipts_cash_request_menu_action_action_picking_type(self):
        return self._get_action('ESS.receipts_cash_request_menu_action')

    def get_intercompany_transaction_action_picking_type(self):
        return self._get_action('ESS.intercompany_transaction_menu_action')

    def get_human_resources_accruals_action_picking_type(self):
        return self._get_action('ESS.human_resources_accruals_menu_action')

    def get_preforma_sales_invoice_menu_action_action_picking_type(self):
        return self._get_action('ESS.preforma_sales_invoice_menu_action')




