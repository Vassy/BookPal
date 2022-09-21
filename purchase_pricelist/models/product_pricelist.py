# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    used_for = fields.Selection([('sale',"Sale"),('purchase',"Purchase")], default='sale')
