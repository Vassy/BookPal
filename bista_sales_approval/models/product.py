# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2022 (https://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = "product.product"

    minimum_sale_price = fields.Float(string="Minimum Sale Price")
