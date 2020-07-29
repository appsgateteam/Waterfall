from odoo import models, fields, api, _
import datetime
from datetime import datetime as dt
import dateutil.parser
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class project_payment_wizard(models.TransientModel):
    _name = 'project.payment.wizard'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    project_ids = fields.Many2many('project.project', 'project_id', string='porjects')
    all_project = fields.Boolean('All Project')
    direct_investment = fields.Selection([
    ('foreign', 'foreign'),
    ('local', 'local'),('self', 'self'),('direct', 'direct'),('banking', 'banking'),
    ('federal', 'federal')], string='Project Type')


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
                'project_ids':project_list,
                'all_project':self.all_project,
                'project_type': self.direct_investment,
            },
        }
        print("////////////////////////  ",data)
        return self.env.ref('sc_account_report.project_payment_report').report_action(self, data=data)

class project_payment_reportRecap(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.sc_account_report.project_payment_report_view'

    @api.multi
    def get_report_values(self, docids, data=None):
        # name = data['form']['name']
        # year = data['form']['year']
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        projects_list = data['form']['project_ids']
        all_project = data['form']['all_project']
        project_type = data['form']['project_type']
        docs = []
        res = {}
        print ("d5lll al report.........................")
        if all_project == True:
            print ("report for all project .....")
            project_list = self.env['project.project'].search([('start_date','>=',date_from),('start_date','<=',date_to)])
            ratif_obj = self.env['sc.account.ratification']
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^6   ",project_list)
            if project_list:
                for pro in project_list:
                    ratif_ids = ratif_obj.search([('project_name','=',pro.id)])
                    print ("********************   ", ratif_ids)
                    if ratif_ids:
                        for ratif in ratif_ids:
                            if ratif.project_name.funding_type == 'foreign':
                                print("1")
                            elif ratif.project_name.funding_type == 'local':
                                print("2")
                            elif ratif.project_name.funding_type == 'self':
                                print("3")
                            elif ratif.project_name.funding_type == 'direct':
                                print("4")
                                res2 = {}
                                if ratif.ratif_payment_id:
                                    for line in ratif.ratif_payment_id:
                                        res2 = {
                                            'date': line.payment_date,
                                            'amount': line.payment_amount,
                                        }
                                res = {
                                    'number' : '4',
                                    'project_name': ratif.project_name.name,
                                    'line': res2,
                                }
                                print ("$$$$$$$$$$$$$$$$$$$44444444    ", res)
                                docs.append(res)
                            elif ratif.project_name.funding_type == 'banking':
                                print("5")
                                docs2 = []
                                project_investment_list = self.env['ratif.investment.main'].search([('project_name','=',ratif.project_name.id)])
                                if project_investment_list:
                                    for line in project_investment_list:
                                        if line.lines_investment:
                                            for l in line.lines_investment:
                                                res2 = {
                                                    'date': l.installment_date,
                                                    'amount': l.installment_amount,
                                                    'state': l.state,
                                                }
                                                docs2.append(res2)
                                res = {
                                    'number' : '5',
                                    'project_name': ratif.project_name.name,
                                    'line': docs2,
                                }
                                print ("$$$$$$$$$$$$$$$$$$$555555    ", res)
                                docs.append(res)
                            else:
                                print("6")
        else:
            print ("report for spicific project type .....")
            if project_type == 'banking':
                print ("++++")
                docs2 = []
                for project in projects_list:
                    project_name = self.env['project.project'].search([('id','=',project)])
                    project_investment_list = self.env['ratif.investment.main'].search([('project_name','=',project)])
                    if project_investment_list:
                        print("1  ",project_investment_list)
                        for line in project_investment_list:
                            print("2")
                            if line.lines_investment:
                                print("3")
                                for l in line.lines_investment:
                                    print("4")
                                    res2 = {
                                        'date': l.installment_date,
                                        'amount': l.installment_amount,
                                        'state': l.state,
                                    }
                                    docs2.append(res2)
                                print("^^  ",docs2)
                            print("5")
                        print("6")
                    print("7")
                    res = {
                        'number' : '5',
                        'project_name': project_name,
                        'line': docs2,
                    }
                    print ("$$$$$$$$$$$$$$$$$$$555555    ", res)
                    docs.append(res)
            else:
                for project in projects_list:
                    ratif_id = self.env['sc.account.ratification'].search([('project_id','=',project)])
                    res2 = {}
                    for ratif in ratif_id:
                        if ratif.ratif_payment_id:
                            for line in ratif.ratif_payment_id:
                                res2 = {
                                    'date': line.payment_date,
                                    'amount': line.payment_amount,
                                }
                        res = {
                            'number' : '4',
                            'project_name': ratif.project_name.name,
                            'line': res2,
                        }
                        print ("$$$$$$$$$$$$$$$$$$$44444444    ", res)
                        docs.append(res)
        print (docs,"<<<<<<<<<<<<<<<<<<<<<<<<<<doc")
        return {
            'doc_ids': data['ids'],
            'doc_model': 'project.payment.wizard',
            'docs': docs,
            'date_from'  : date_from,
            'date_to' : date_to,
        }