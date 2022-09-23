# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    used_for = fields.Selection([('sale',"Sale"),('purchase',"Purchase")], default='sale')
    on_order = fields.Boolean(string="On Order")
    product_pricelist_order_ids = fields.One2many('product.pricelist.order', 'pricelist_id', string="Items")

    def _get_partner_pricelist_multi_search_domain_hook(self, company_id):
        res = super(ProductPricelist, self)._get_partner_pricelist_multi_search_domain_hook(company_id)
        res.append(('used_for', '=', 'sale'))
        return res

class ProductPricelistOrder(models.Model):
    _name = "product.pricelist.order"
    _description = "Product Pricelist On Order"

    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    sequence = fields.Integer(string="Sequence")
    order_amount = fields.Float(string="Order Amount (>=)")
    discount = fields.Float(string="Discount (%)")