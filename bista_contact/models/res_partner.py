# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    type = fields.Selection(selection_add=[
                            ('return', 'Return Address'),
                            ('warehouse', 'Warehouse Address'),]
                            )

    # Contact Details
    customer_status = fields.Selection([('pending', 'Prospect'),
                                        ('active', 'Active'), ('idle', 'Idle'),
                                        ('churned', 'Churned'), ('dead', 'Dead'),
                                        ('supplier', 'Supplier')])
    dead_resone = fields.Char('Dead Reasone', attrs="{'invisible': [('customer_status', '!=','dead')]}")
    dead_date = fields.Datetime('Dead Date', attrs="{'invisible': [('customer_status', '!=','dead')]}")
    do_not_call = fields.Boolean('DO Not Call')

    # Important Details
    source = fields.Char('Source')
    referal_source = fields.Char('Referral Source')
    source_notes = fields.Char('Source Notes')

    # Order Information

    avg_order_value = fields.Char('Average Order Value',compute='get_avg_order_value')
    first_order_date = fields.Datetime('First Order Date',compute='get_first_order_date')
    last_order_date = fields.Datetime('Last Order Date',compute='get_first_order_date')
    sale_product_ids = fields.Many2many('product.product',string='Sale Products',compute='get_ordered_product')

    # To get first order date and last order date
    def get_first_order_date(self):
        self.first_order_date = False
        self.last_order_date =  False
        if self.sale_order_count > 0:
            date_list= self.sale_order_ids.mapped('date_order')
            date_list.sort()
            self.first_order_date = date_list[0]
            self.last_order_date = date_list[-1]

    # To calculate average amount of customers's order
    def get_avg_order_value(self):
        self.avg_order_value = 0
        if self.sale_order_count > 0:
            amount= self.sale_order_ids.mapped('amount_total')
            self.avg_order_value = sum(amount)/self.sale_order_count

    #To get Sale Products
    def get_ordered_product(self):
        self.sale_product_ids = False
        if self.sale_order_count > 0:
           product_list = self.sale_order_ids.mapped('order_line').filtered(
                lambda a: a.product_id.detailed_type != 'service').mapped('product_id')
           self.sale_product_ids=[(6,0,product_list.ids)]

    def _avatar_get_placeholder_path(self):
        if self.type == 'return':
            return "bista_contact/static/img/return.jpg"
        if self.type == 'warehouse':
            return "bista_contact/static/img/warehouse.png"
        return super()._avatar_get_placeholder_path()
