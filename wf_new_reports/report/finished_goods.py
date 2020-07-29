from odoo import api, models, _
from odoo.exceptions import except_orm, ValidationError ,UserError


class ReportFinishedGoodsReport(models.AbstractModel):
    _name = 'report.wf_new_reports.report_finished_goods'

    @api.model
    def _get_report_values(self, docids, data=None):
        d_from = data['form']['from']
        d_to = data['form']['to']
        show = data['form']['show']
        # productss = data['form']['products']
        appointment_list = []
        array = []


        com = self.env['mrp.production'].search([('state','=','done'),('date_finished','>=',d_from),('date_finished','<=',d_to)])
        client = ''
        status = ''
        for l in com:
            # delivery_date = l.date_planned_start_wo
            date_finished = l.date_finished
            so = l.origin
            mo = l.name
            # cost = l.final_total_actual_cost
            # if l.finished_move_line_ids:
            #     des = l.finished_move_line_ids.name
            #     qty = l.finished_move_line_ids.qty_done
            #     lot = l.finished_move_line_ids.lot_id.name
            # state = l.state
            # state2 = l.state

            if l.origin:
                cos = self.env['sale.order'].search([('name','=',l.origin)])
                client = cos.partner_id.name
            i = 1
            for y in data['form']['category']:
                for fin in l.finished_move_line_ids:
                    des = fin.product_id.name
                    qty = fin.qty_done
                    lot = fin.lot_id.name
                    if fin.lot_id.product_qty != 0:
                        if y['id'] == fin.product_id.product_tmpl_id.categ_id.id :
                            # for product in data['form']['products']:
                            if show == True:
                                for x in l.move_raw_ids:
                                    if data['form']['products']:
                                        for product in data['form']['products']:
                                            if product['id'] == x.product_id.product_tmpl_id.categ_id.id:
                                                if i != 1:
                                                    # delivery_date = ''
                                                    date_finished = ''
                                                    so = ''
                                                    mo = ''
                                                    lot = ''
                                                    qty = ''
                                                    client = ''
                                                    des = ''
                                                    # cost = ''
                                                    # state = ''
                                                
                                                vals = {
                                                    'so':so,
                                                    'mo':mo,
                                                    'lot':lot,
                                                    'qty':qty,
                                                    'des':des,
                                                    # 'cost':cost,
                                                    # 'state':state,
                                                    # 'delivery_date':delivery_date,
                                                    'date_finished':date_finished,
                                                    'client':client,
                                                    'product':x.product_id.name,
                                                    # 'product_code':x.product_id.default_code,
                                                    # 'remark':status
                                                }
                                                appointment_list.append(vals)
                                                i = i + 1
                                    else:
                                        if i != 1:
                                                # delivery_date = ''
                                            date_finished = ''
                                            so = ''
                                            mo = ''
                                            lot = ''
                                            qty = ''
                                            client = ''
                                            des = ''
                                            # cost = ''
                                            # state = ''
                                        
                                        vals = {
                                            'so':so,
                                            'mo':mo,
                                            'lot':lot,
                                            'qty':qty,
                                            'des':des,
                                            # 'cost':cost,
                                            # 'state':state,
                                            # 'delivery_date':delivery_date,
                                            'date_finished':date_finished,
                                            'client':client,
                                            'product':x.product_id.name,
                                            # 'product_code':x.product_id.default_code,
                                            # 'remark':status
                                        }
                                        appointment_list.append(vals)
                                        i = i + 1
                            else:
                                vals = {
                                        'so':so,
                                        'mo':mo,
                                        'lot':lot,
                                        'qty':qty,
                                        'des':des,
                                        # 'cost':cost,
                                        # 'state':state,
                                        # 'delivery_date':delivery_date,
                                        'date_finished':date_finished,
                                        'client':client,
                                        'product':'',
                                        # 'show':show,
                                        # 'product_code':x.product_id.default_code,
                                        # 'remark':status
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
            'show':show,
            'docs': appointment_list,
        }
