from odoo import models, fields, api, _
import datetime
from datetime import datetime as dt
import dateutil.parser
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class bank_move_wizard(models.TransientModel):
    _name = 'bank.move.wizard'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    bank_id = fields.Many2one('account.account', domain=[('user_type_id','=',3)], string='Bank')
    project_ids = fields.Many2many('project.project', 'bank_project_rel', 'bank_id', 'project_id', string='porjects')
    all_project = fields.Boolean('All Project')

    def print_report(self):
        project_list = []
        if self.project_ids:
            for project in self.project_ids:
                project_list.append(project.id)
        data = {
            'ids': self.ids,
            'model': self._name,
            'form' : {
                'date_from':self.date_from,
                'date_to':self.date_to,
                'bank_id':self.bank_id.id,
                'project_ids':project_list,
                'all_project':self.all_project,
            },
        }
        print("1       ////////////////////////  ",data)
        return self.env.ref('sc_account_report.bank_move_report').report_action(self, data=data)


class bank_move_reportRecap(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """
    _name = 'report.sc_account_report.bank_move_report_view'

    @api.multi
    def get_report_values(self, docids, data=None):
        print ("2       [[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]  ",data)
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        bank_id = data['form']['bank_id']
        projects = data['form']['project_ids']
        all_project = data['form']['all_project']


        order_ids = self.env['standing.payment.order'].search([('bank','=',bank_id)])
        bank_name = self.env['account.account'].search([('id','=',bank_id)]).name
        invesment_obj = self.env['ratif.investment.main']
        investment_lines_obj = self.env['ratification.bank.investment']
        investment_project = []

        listt2 = [{
            'bank': bank_name,
            'date_from': date_from,
            'date_to': date_to,
            'all_project': all_project,
            'project_ids': len(projects),
        }]
        print("3     CCCCCCCCCCCCCCCCCCCCCCCCCCCCClistt2   ",listt2)

        res = {}
        listt = []
        if all_project == True or len(projects) > 1:
            if order_ids:
                for order in order_ids:
                    for project in order.ratification_id:
                        investment_project = invesment_obj.search([('date_from','>=',date_from),('date_to','<=',date_to)])
                count = 0
                for project_invest in investment_project:
                    payed_amount = 0.00
                    residual_amount = 0.00
                    investment_line_id = investment_lines_obj.search([('ratif_lines','=',project_invest.id)])
                    for i in investment_line_id:
                        count +=1
                        if i.state == "payed":
                            payed_amount += i.installment_amount
                        else:
                            residtual_amount += i.installment_amount
                    res = {
                        'project_name': project_invest.project_name.name,
                        'total': (payed_amount + residual_amount),
                        'payed': payed_amount,
                        'residual': residual_amount,
                        'count': count,
                    }
                    listt.append(res)
                print ("4     CCCCCCCCCCCCCCCCCCCCCCCCCCCCClistt   ",listt)
        else:
            print("ppppppppppppppppppppppppp   ",order_ids)
            
            for project in order_ids:
                print(";;;;;;;;;;;;;  ",project)
                investment_project = invesment_obj.search([('project_name','=',project.ratification_id.project_name.id),('date_from','>=',date_from),('date_to','<=',date_to)])
            print("))))))))))))))))))))    ", investment_project)
            count = 0
            for project_invest in investment_project:
                investment_list = []
                for i in project_invest.lines_investment:
                    res = {
                        'installment_number': i.installment_number,
                        'project_name': project_invest.project_name.name,
                        'date': i.installment_date,
                        'amount': i.installment_amount,
                        'state': i.state,
                    }
                    investment_list.append(res)
                print ("3     CCCCCCCCCCCCCClistt   ",listt)
                listt.append(investment_list)
            print ("4     CCCCCCCCCCCCCCCCCCCCCCCCCCCCClistt   ",listt)
        return {
            'doc_ids': data['ids'],
            'doc_model': 'bank.move.wizard',
            'bank': bank_id,
            'date_from': date_from,
            'date_to': date_to,
            'all_project': all_project,
            'project_ids': len(projects),
            'docs': listt,
        }

