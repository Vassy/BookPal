# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    used_for = fields.Selection(
        [("sale", "Sale"), ("purchase", "Purchase")], default="sale"
    )
    on_order = fields.Boolean(string="On Purchase Order")
    apply_on = fields.Selection(
        [("order_amount", "Order Amount"), ("order_qty", "Order Quantity")],
        string="Apply On",
    )
    product_pricelist_order_ids = fields.One2many(
        "product.pricelist.order", "pricelist_id", string="Items"
    )
    discount_policy = fields.Selection(
        [
            ("with_discount", "Discount included in the price"),
            ("without_discount", "Show public price & discount to the vendor"),
        ],
        default="without_discount",
    )

    @api.onchange("product_pricelist_order_ids")
    def onchange_product_pricelist_order_ids(self):
        pricelist_line_ids = self.product_pricelist_order_ids.sorted(
            "from_value", reverse=True
        )
        count = 1
        for line in pricelist_line_ids:
            line.sequence = count
            count += 1

    @api.onchange("used_for")
    def onchange_used_for(self):
        if self.used_for == "sale":
            self.on_order = False
            self.apply_on = False

    def _get_partner_pricelist_multi_search_domain_hook(self, company_id):
        res = super(
            ProductPricelist, self
        )._get_partner_pricelist_multi_search_domain_hook(company_id)
        res.append(("used_for", "=", "sale"))
        return res

    def get_pricelist_line_based_on_order(self, amount, quantity):
        value = quantity if self.apply_on == "order_qty" else amount
        pricelist_order_line = self.product_pricelist_order_ids.filtered(
            lambda x: x.from_value <= value and (x.to_value >= value or x.to_value == 0)
        ).sorted("sequence")
        pricelist_order_line = (
            pricelist_order_line[0] if pricelist_order_line else pricelist_order_line
        )
        return pricelist_order_line


class ProductPricelistOrder(models.Model):
    _name = "product.pricelist.order"
    _description = "Product Pricelist On Order"

    pricelist_id = fields.Many2one("product.pricelist", string="Pricelist")
    sequence = fields.Integer(string="Sequence")
    from_value = fields.Float(string="From")
    to_value = fields.Float(string="To")
    discount = fields.Float(string="Discount (%)")
