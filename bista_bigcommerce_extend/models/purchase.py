# -*- coding: utf-8 -*-

from odoo import models, fields


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    product_format = fields.Char(related="product_id.product_format")
