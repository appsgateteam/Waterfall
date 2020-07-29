from odoo import api, models, _
from odoo.exceptions import except_orm, ValidationError ,UserError


class reportmrpworkorderReport(models.AbstractModel):
    _name = 'report.wf_new_reports.report_mrp_workorder'

    @api.model
    def _get_report_values(self, docids, data=None):
        # report_obj = self.env['ir.actions.report']
        # report = report_obj._get_report_from_name('wf_new_reports.report_mrp_workorder')
        # model = self.env.context.get('active_model')
        # pur = self.env['mrp.production'].browse(self.env.context.get(self))
        # raise UserError(_(self.id))
        # appointment_list = []
        # com = self.env['sale.order'].search([('name','=',pur.origin)])
        # for x in pur:
        #     raise UserError(_(x.origin))
        # if com:
        #     for l in com:
        #         appointment_list.append(l)


        return {
            'doc_ids': docids,
            'doc_model': 'mrp.production',
            'docs': self,
            # 'sale':appointment_list,
        }
