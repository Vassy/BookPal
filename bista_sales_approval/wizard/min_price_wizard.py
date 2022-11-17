# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class ProductMinPrice(models.TransientModel):
    _name = "min.price.wiz"
    _description = "Min Price Wizard"

    sale_id = fields.Many2one('sale.order')
    order_line_ids = fields.Many2many('sale.order.line', string='Lines')

    def send_order_for_review(self):
        sale_order = self.sale_id
        if sale_order:
            sale_order.state = 'min_price_review'
            context = self._context
            sale_order._create_sale_approval_log(sale_order.id, context.get('uid'),
                                                 'Quote Under Review for Product Price')
