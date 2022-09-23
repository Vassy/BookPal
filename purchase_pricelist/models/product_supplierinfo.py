# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    vendor_pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")

    # @api.onchange("name")
    # def onchange_name(self):
    #     self.vendor_pricelist_id = self.name.property_product_vendor_pricelist
