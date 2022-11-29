# -*- coding: utf-8 -*-

from odoo import models, api, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    property_product_vendor_pricelist = fields.Many2one(
        "product.pricelist",
        help="This pricelist will be used, instead of the default one, "
        "for purchase to the current partner",
    )

    @api.onchange("property_purchase_currency_id")
    def onchange_property_purchase_currency_id(self):
        if (
            self.property_purchase_currency_id
            != self.property_product_vendor_pricelist.currency_id
            and self.property_product_vendor_pricelist
        ):
            self.property_product_vendor_pricelist = False
            msg = "Vendor pricelist needs to reset due to change in currency."
            return {"warning": {"title": "Vendor Pricelist Change", "message": msg}}
