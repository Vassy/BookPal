# -*- coding: utf-8 -*-

from odoo import models, api, fields


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    applied_product_pricelist = fields.Boolean(string="Applied Product Pricelist")

    @api.depends('product_id', 'company_id', 'currency_id', 'product_uom', 'supplier_id', 'product_uom_qty')
    def _compute_purchase_price(self):
        for line in self:
            if not line.product_id or not line.supplier_id:
                line.purchase_price = 0.0
                continue
            line = line.with_company(line.company_id)
            # product_cost = line.product_id.standard_price
            product_cost = line.get_vendor_price()
            if not product_cost:
                line.apply_on_order_vendor_price()
                continue
            line.purchase_price = line._convert_price(product_cost, line.product_id.uom_id)
            line.applied_product_pricelist = True

    def get_vendor_price(self):
        seller_ids = self.product_id.seller_ids.filtered(lambda x:x.name==self.supplier_id)
        if not seller_ids:
            return 0

        seller = seller_ids and seller_ids[0]
        if not seller.vendor_pricelist_id:
            return 0

        product_cost = 0
        pricelist_id = seller.vendor_pricelist_id
        product_context = dict(
            self.env.context,
            partner_id=self.supplier_id.id,
            date=self.order_id.date_order,
            uom=self.product_uom.id,
        )
        price, rule_id = pricelist_id.with_context(
            product_context
        ).get_product_price_rule(
            self.product_id, self.product_uom_qty or 1.0, self.supplier_id
        )
        if rule_id:
            rule = self.env["product.pricelist.item"].browse(rule_id)
            product_cost = rule._compute_price(
                seller.price, self.product_uom, self.product_id, self.product_uom_qty
            )
        return product_cost

    def apply_on_order_vendor_price(self):
        pricelist_id = self.supplier_id.property_product_vendor_pricelist
        order_lines = self.order_id.order_line.filtered(lambda x:x.supplier_id == self.supplier_id)
        on_order_total = sum([line.product_uom_qty*line.price_unit for line in order_lines])
        on_order_quantity = sum(order_lines.mapped('product_uom_qty'))
        pricelist_line = pricelist_id.get_pricelist_line_based_on_order(
                on_order_total, on_order_quantity)
        for line in order_lines:
            line.purchase_price = (line.price_unit - (line.price_unit*pricelist_line.discount)/100)

    def action_update_product_cost(self):
        self.apply_on_order_vendor_price()
