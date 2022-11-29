# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    vendor_pricelist_id = fields.Many2one("product.pricelist", string="Pricelist")
