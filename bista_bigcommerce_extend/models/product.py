# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = "product.product"

    avatax_category_id = fields.Many2one(
        default=lambda product: product._default_avatax_category_id()
    )

    def _default_avatax_category_id(self):
        return self.env["ir.model.data"]._xmlid_to_res_id("account_avatax.PB100000")
