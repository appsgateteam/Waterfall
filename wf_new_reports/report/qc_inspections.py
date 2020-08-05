from odoo import api, models, _
from odoo.exceptions import except_orm, ValidationError ,UserError
from datetime import datetime, timedelta , date


class ReportQualityCheckRe(models.AbstractModel):
    _name = 'report.wf_new_reports.report_quality_check_re'

    @api.model
    def _get_report_values(self, docids, data=None):
        # d_from = data['form']['from']
        # d_to = data['form']['to']
        pick = data['form']['picking']
        production = data['form']['production']
        pick_names = data['form']['picking_name']
        production_name = data['form']['production_name']
        # productss = data['form']['products']
        appointment_list = []
        array = []
        quality_point = ''
        types = ''
        loc = ''
        note = ''
        source = ''
        loc = ''
        qty = 0.0

        if pick and production:
            raise UserError('You can select only one type')
        if pick:
            pick_name = pick_names
            com = self.env['quality.check'].search([('picking_id','=',pick),('quality_state','!=','close')])
            for l in com:
                if l.point_id:
                    quality_point =  l.point_id.name
                    types = l.point_id.title
                if l.notes:
                    note = l.notes
                source = l.source_origin
                loc = l.picking_id.location_dest_id.name
                lot = ''
                coms = self.env['stock.picking'].search([('id','=',pick)])
                for x in coms:
                    for pro in x.move_ids_without_package:
                        if l.product_id.id == pro.product_id.id:
                            qty = pro.product_uom_qty
                        for line in pro.move_line_ids:
                            if line.lot_id:
                                if lot == '':
                                    lot = line.lot_id.name
                                else:
                                    lot = line.lot_id.name + ',' + lot
                vals = {
                        'team':l.team_id.name,
                        'quality_point' :quality_point,
                        'product':l.product_id.name,
                        'lot':lot,
                        'note':note,
                        'employee':l.user_id.name,
                        'state':l.quality_state,
                        'qty':qty,
                        
                    }
                appointment_list.append(vals)
        if production:
            pick_name = production_name
            com = self.env['quality.check'].search([('quality_state','!=','close')])
            for l in com:
                if l.workorder_id.production_id.id == production:
                    if l.point_id:
                        quality_point =  l.point_id.name
                        types = l.point_id.title
                    if l.notes:
                        note = l.notes
                    
                    loc = 'Production'
                    source = l.source_origin_mo
                    # coms = self.env['stock.picking'].search([('id','=',pick)])
                    # for x in coms:
                    #     for pro in x.move_ids_without_package:
                    #         if l.product_id.id == pro.product_id.id:
                    #             qty = pro.product_uom_qty
                    vals = {
                            'team':l.team_id.name,
                            'quality_point' :quality_point,
                            'product':l.component_id.name,
                            'lot':l.lot_id.name,
                            'note':note,
                            # 'source':l.source_origin_mo,
                            'employee':l.user_id.name,
                            'state':l.quality_state,
                            'qty':l.qty_done,
                            
                        }
                    appointment_list.append(vals)
        
        # array.append({
        #     'quality_point':quality_point,
        #     'type':types,
        #     'location':loc,
        #     'date':date.today(),
        #     'note':note,
        # })
        #     # i = i + 1




        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'pick_name' :pick_name,
            'source':source,
            # 'quality_point' :quality_point,
            'type' :types,
            'location' :loc,
            # 'note' :note,
            'date' :date.today(),
            'docs': appointment_list,
            'doc': array,
        }
