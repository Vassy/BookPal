# -*- coding: utf-8 -*-

from odoo import models, api, fields


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    purchase_price = fields.Float(copy=False)

    @api.depends(
        "route_id",
        "supplier_id",
        "purchase_line_ids.price_unit",
        "move_ids.created_purchase_line_id.price_unit",
        "move_ids.move_orig_ids.purchase_line_id.price_unit",
        "virtual_available_at_date",
        "order_id.order_line.product_uom_qty",
    )
    def _compute_purchase_price(self):
        for line in self:
            if not line.product_id or not line.supplier_id:
                line.purchase_price = 0
                continue
            if line.state not in ["sale", "done"]:
                line.purchase_price = line.get_vendor_price()
            else:
                purchase_line_id = (
                    line.purchase_line_ids
                    | line.move_ids.created_purchase_line_id
                    | line.move_ids.move_orig_ids.purchase_line_id
                )
                if purchase_line_id.product_qty == line.product_uom_qty:
                    line.purchase_price = purchase_line_id.price_unit
                else:
                    total_qty = purchase_line_id.product_qty
                    total_price = purchase_line_id.price_subtotal
                    remaining_qty = line.product_uom_qty - total_qty
                    for layer_id in line.product_id.stock_valuation_layer_ids:
                        if remaining_qty <= layer_id.remaining_qty:
                            total_qty += remaining_qty
                            total_price += remaining_qty * layer_id.unit_cost
                            break
                        else:
                            total_qty += layer_id.remaining_qty
                            total_price += layer_id.remaining_qty * layer_id.unit_cost
                            remaining_qty -= layer_id.remaining_qty
                    line.purchase_price = total_price / total_qty

    def get_vendor_price(self):
        self.ensure_one()
        product_cost = 0
        seller_id = self.product_id.seller_ids.filtered(
            lambda seller: seller.name == self.supplier_id
        )[0]
        if not seller_id or not seller_id.vendor_pricelist_id:
            return self.apply_on_order_vendor_price(seller_id)

        product_context = dict(
            self._context, date=self.order_id.date_order, uom=self.product_uom.id
        )
        price, rule_id = seller_id.vendor_pricelist_id.with_context(
            product_context
        ).get_product_price_rule(
            self.product_id, self.product_uom_qty or 1.0, self.supplier_id
        )
        if rule_id:
            rule = self.env["product.pricelist.item"].browse(rule_id)
            product_cost = rule._compute_price(
                seller_id.price, self.product_uom, self.product_id, self.product_uom_qty
            )
        return product_cost

    def apply_on_order_vendor_price(self, seller_id):
        pricelist_id = self.supplier_id.property_product_vendor_pricelist
        order_lines = self.order_id.order_line.filtered(
            lambda x: x.supplier_id == self.supplier_id
        )
        on_order_total = sum(
            [line.product_uom_qty * line.price_unit for line in order_lines]
        )
        on_order_quantity = sum(order_lines.mapped("product_uom_qty"))
        pricelist_line = pricelist_id.get_pricelist_line_based_on_order(
            on_order_total, on_order_quantity
        )
        if pricelist_line:
            return self.price_unit - (self.price_unit * pricelist_line.discount) / 100
        elif seller_id:
            return seller_id.price
        else:
            return 0
