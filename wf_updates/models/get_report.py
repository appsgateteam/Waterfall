# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class ReportSaleSummaryReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.wf_updates.sale_summary_report_view'

    


    

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        sales_person = data['form']['sales_person']
        sales_person_name = data['form']['sales_person_name']


        SO = self.env['sale.order']
        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)
        delta = timedelta(days=1)


        date_ob_star = datetime.strptime(date_start, DATE_FORMAT)

        date_ob_end = datetime.strptime(date_end,DATE_FORMAT)

        
            


        docs = []
        while start_date <= end_date:
            date = start_date
            start_date += delta

            print(date, start_date)
            orders = SO.search([
                ('user_id', '=', sales_person),
                ('confirmation_date', '>=', date.strftime(DATETIME_FORMAT)),
                ('confirmation_date', '<', start_date.strftime(DATETIME_FORMAT)),
                ('state', 'in', ['draft','sale', 'done',]),
                 ],order='name desc')
            
            for rec in orders: 

                if rec.inv_date and rec.inv_date < date_ob_star.date():
                    continue

                if rec.inv_date and rec.inv_date > date_ob_end.date():
                    continue
                    

                for l in rec.order_line:
                    if data['form']['category']:
                        for y in data['form']['category']:
                            if y['id'] == l.product_id.product_tmpl_id.categ_id.id:
                                vaul = {
                                    'date': rec.date_order,
                                    'Product' : l.product_id.name,
                                    'partner' : rec.partner_id.name,
                                    'company': self.env.user.company_id,
                                    'sales order no' : rec.name,
                                    'invoice status' : rec.invoice_status,
                                    'salesperson' : rec.user_id.name,
                                    'value' : l.price_subtotal,
                                    'state' : rec.receive_state,
                                    'country' : rec.country.name,
                                    'po_date' : rec.cus_date,
                                    'po_no' : rec.client_order_ref or '',
                                    'paid_amount' : rec.paid_amount,
                                    'bal_amount' : rec.bal_amount,
                                    'inv_date' : rec.inv_date
                                }
                                docs.append(vaul)
                    else:
                        vaul = {
                            'date': rec.date_order,
                            'Product' : l.product_id.name,
                            'partner' : rec.partner_id.name,
                            'company': self.env.user.company_id,
                            'sales order no' : rec.name,
                            'invoice status' : rec.invoice_status,
                            'salesperson' : rec.user_id.name,
                            'value' : l.price_subtotal,
                            'state' : rec.receive_state,
                            'country' : rec.country.name,
                            'po_date' : rec.cus_date,
                            'po_no' : rec.client_order_ref or '',
                            'paid_amount' : rec.paid_amount,
                            'bal_amount' : rec.bal_amount,
                            'inv_date' : rec.inv_date
                        }
                        docs.append(vaul)


        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            'sales_person': sales_person,
            'sales_person_name': sales_person_name,
            'docs': docs,
        }