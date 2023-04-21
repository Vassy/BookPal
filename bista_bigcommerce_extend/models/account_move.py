# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_format = fields.Char(related="product_id.product_format")
