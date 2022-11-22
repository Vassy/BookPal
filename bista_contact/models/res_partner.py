# -*- coding: utf-8 -*-
from odoo import fields, models


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
    block_reason=fields.Char('Reason')
    block=fields.Boolean('Block')

    def get_first_order_date(self):
        """To get first order date and last order date"""
        self.first_order_date = False
        self.last_order_date =  False
        if self.sale_order_count > 0:
            date_list= self.sale_order_ids.mapped('date_order')
            date_list.sort()
            if date_list:
                self.first_order_date = date_list[0]
                self.last_order_date = date_list[-1]

    def get_avg_order_value(self):
        """To calculate average amount of customers's order"""
        self.avg_order_value = 0
        if self.sale_order_count > 0:
            amount= self.sale_order_ids.mapped('amount_total')
            self.avg_order_value = sum(amount)/self.sale_order_count

    def get_ordered_product(self):
        """To get Sale Products"""
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

    def open_block_unblock_wizard(self):
        """ to block/unblock contact """
        partner_ids = self.ids
        if self.env.context.get('block'):
             return {
                     'name': 'Details',
                     'type': 'ir.actions.act_window',
                     'view_mode': 'form',
                     "view_type": "form",
                     'res_model': 'contact.status.update',
                     'target': 'new',
                     'view_id': self.env.ref
                     ('bista_contact.customer_block_reasone_partner').id,
                     'context': {'partner_ids': partner_ids,'default_block': True},
                 }
        if self.env.context.get('unblock'):
             return {
                     'name': 'Details',
                     'type': 'ir.actions.act_window',
                     'view_mode': 'form',
                     "view_type": "form",
                     'res_model': 'contact.status.update',
                     'target': 'new',
                     'view_id': self.env.ref
                     ('bista_contact.customer_block_reasone_partner').id,
                     'context': {'partner_ids': partner_ids,'default_block': False},
                 }
