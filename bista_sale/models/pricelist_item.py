from odoo import fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    discount_amount = fields.Float(
        'Discount Price', compute="_cal_discount_price")

    def _cal_discount_price(self):
        """Calculated the discount price."""
        for item in self:
            item.discount_amount = 0
            if item.product_tmpl_id and \
                item.product_tmpl_id.list_price and \
                    item.percent_price:
                dis_amt = (item.product_tmpl_id.list_price *
                           item.percent_price) / 100
                item.discount_amount = item.product_tmpl_id.list_price - \
                    dis_amt
