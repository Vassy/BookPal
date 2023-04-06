# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    vendor_pricelist_id = fields.Many2one("product.pricelist", string="Pricelist")

    @api.onchange("name")
    def _onchange_name(self):
        res = super()._onchange_name()
        if self.name and self.product_tmpl_id and self.product_tmpl_id.list_price:
            self.price = self.product_tmpl_id.list_price
        return res
