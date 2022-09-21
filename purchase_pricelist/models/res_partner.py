# -*- coding: utf-8 -*-
from odoo import models, api, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    property_product_vendor_pricelist = fields.Many2one(
        'product.pricelist', 'Pricelist', company_dependent=False,
        help="This pricelist will be used, instead of the default one, for purchase to the current partner")
