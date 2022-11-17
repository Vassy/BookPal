##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, models, fields
from datetime import datetime


class ProductProduct(models.Model):
    _inherit = "product.product"

    minimum_sale_price = fields.Float(string='Minimum Sale Price')

