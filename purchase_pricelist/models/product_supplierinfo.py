# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    vendor_pricelist_id = fields.Many2one("product.pricelist", string="Pricelist")

    # def write(self, vals):
    #     res = super(ProductSupplierInfo, self).write(vals)
    #     for rec in self:
    #         if rec.product_id and rec.product_id.list_price != rec.price:
    #             rec.price = rec.product_id.list_price
    #         elif rec.product_tmpl_id and rec.product_tmpl_id.list_price != rec.price:
    #             rec.price = rec.product_tmpl_id.list_price
    #     return res

    @api.onchange('name')
    def _onchange_name(self):
        res = super()._onchange_name()
        if self.name and self.product_tmpl_id and self.product_tmpl_id.list_price:
            self.price = self.product_tmpl_id.list_price
        return res
