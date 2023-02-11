# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    vendor_pricelist_id = fields.Many2one("product.pricelist", string="Pricelist")

    def write(self, vals):
        res = super(ProductSupplierInfo, self).write(vals)
        if self.product_id:
            self.price = self.product_id.list_price
        elif self.product_tmpl_id:
            self.price = self.product_tmpl_id.list_price
        return res