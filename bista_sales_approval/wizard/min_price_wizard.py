# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2022 (https://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class ProductMinPrice(models.TransientModel):
    _name = "min.price.wiz"
    _description = "Min Price Wizard"

    sale_id = fields.Many2one("sale.order")
    order_line_ids = fields.Many2many("sale.order.line", string="Lines")

    def send_order_for_review(self):
        sale_order = self.sale_id
        if sale_order:
            sale_order.state = "min_price_review"
            sale_order._create_sale_approval_log(
                self._context.get("uid"),
                "Quote Under Review for Product Price",
            )
