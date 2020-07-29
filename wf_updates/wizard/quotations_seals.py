# -*- coding: utf-8 -*-

from odoo import api, fields, models


class quotations_seals(models.TransientModel):
    _name = 'quotations.seals'
    _description = 'Get Quotations About Date'


    date_start  = fields.Date(string="Start Date" , required=True, default=fields.Date.today)
    date_end  = fields.Date(string="End Date" , required=True, default=fields.Date.today)
    sales_person = fields.Many2one('res.users', string="Salesperson",required=True,index=True, default=lambda self: self.env.user)
    products = fields.Many2many('product.category','pro_ids','prod_cat_ids',string="Products")


    able_to_modify_product = fields.Boolean(compute="set_access_for_product", default=False , string='Is user able to modify product?')


    @api.depends('sales_person')
    def set_access_for_product(self):
        self.able_to_modify_product = self.env['res.users'].has_group('sales_team.group_sale_manager')

    
            

      
        

    @api.multi
    def get_report(self):
        pro = []
        for l in self.products:
            proj = {
                'id':l.id,
                'name':l.name,
            }
            pro.append(proj)
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end,'sales_person': self.sales_person.id,'sales_person_name': self.sales_person.name,'category': pro,
            },
        }
         # ref `module_name.report_id` as reference.
        return self.env.ref('wf_updates.sale_summary_report').report_action(self, data=data)

       

# class product_template(models.Model):
#     _inherit="quotations.seals"


#     able_to_modify_product = fields.Boolean(compute=set_access_for_product, string='Is user able to modify product?')


#     @api.one
#     def set_access_for_product(self):
#         self.able_to_modify_product = self.env['res.users'].has_group('wf_updates.group_sale_top_manager')

