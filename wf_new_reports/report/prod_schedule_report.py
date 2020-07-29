from odoo import api, models, _
from odoo.exceptions import except_orm, ValidationError ,UserError


class productionscheduleReport(models.AbstractModel):
    _name = 'report.wf_new_reports.report_production_schedule'

    @api.model
    def _get_report_values(self, docids, data=None):
        d_from = data['form']['from']
        d_to = data['form']['to']
        appointment_list = []
        array = []


        com = self.env['mrp.production'].search([('date_planned_start_wo','>=',d_from),('date_planned_start_wo','<=',d_to)])
        client = ''
        status = ''
        for l in com:
            delivery_date = l.date_planned_start_wo
            date_finished = l.date_finished
            so = l.origin
            mo = l.name
            des = l.product_id.name
            state = l.state
            state2 = l.state

            if l.origin:
                cos = self.env['sale.order'].search([('name','=',l.origin)])
                client = cos.partner_id.name
            i = 1
            for y in data['form']['category']:
                for x in l.move_raw_ids:
                    if y['id'] == x.product_id.categ_id.id :
                        if i != 1:
                            delivery_date = ''
                            date_finished = ''
                            so = ''
                            mo = ''
                            client = ''
                            des = ''
                            state = ''
                        if x.product_uom_qty == x.reserved_availability:
                            status = 'Available'
                        elif x.reserved_availability <= x.product_uom_qty and x.reserved_availability > 0 :
                            status = 'Partial Availability'
                        else:
                            status = 'Not Available'
                        
                        if state2 == 'done':
                            status = 'Consumed'
                        if state2 == 'cancel':
                            status = 'Not Available'
                        vals = {
                            'so':so,
                            'mo':mo,
                            'des':des,
                            'state':state,
                            'delivery_date':delivery_date,
                            'date_finished':date_finished,
                            'client':client,
                            'product':x.product_id.name,
                            'product_code':x.product_id.default_code,
                            'remark':status
                        }
                        appointment_list.append(vals)
                        i = i + 1
            # data = {
                
            #     'mat':array,
            # }
            # appointment_list.append(data)
            
                



        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'd_from' :d_from,
            'd_to':d_to,
            'docs': appointment_list,
        }
