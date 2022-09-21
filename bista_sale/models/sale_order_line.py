# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_image = fields.Image(string="Product Image")


    @api.onchange('product_image', 'product_id')
    def get_product_image(self):
        print('image',self.product_image,self.product_id)
        self.product_image = self.product_id.image_1920
