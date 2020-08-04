# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def cron_overdue_customer(self):
        for rec in self:
            rec.ensure_one()
            overdue_list = []
            data = {}
            duecount = 0
            current_date = datetime.today().strftime('%Y-%m-%d')
            user = self.env.user
            overdue = self.env['account.invoice'].search(
                [('date_due', '<=', current_date), ('state', '=', 'open'), ('user_id', '=', rec.user_id.id)])
            for res in overdue:
                overdue_content = {}
                duecount = duecount + 1
                overdue_content['inv_count'] = duecount
                overdue_content['inv_no'] = res.number
                overdue_content['customer'] = res.partner_id.name
                overdue_content['inv_date'] = res.date_invoice
                overdue_content['due_date'] = res.date_due
                overdue_content['inv_amt'] = res.amount_total
                overdue_content['due_amt'] = res.residual
                overdue_list.append(overdue_content)
            data['invoice_overdue'] = overdue_list
            try:
                template_id = self.env.ref('waterfall_report_enhancement.customer_overdue_mail_report')
            except ValueError:
                template_id = False
            mail_template = self.env['mail.template'].browse(template_id.id)
            ctx = self.env.context.copy()
            for key, value in data.items():
                ctx['data'] = value
            mail_template.with_context(ctx).send_mail(rec.id, force_send=True, raise_exception=True)
        return True