# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # adding discount to depends
    @api.depends("discount")
    def _compute_amount(self):
        return super()._compute_amount()

    def _prepare_compute_all_values(self):
        vals = super()._prepare_compute_all_values()
        vals.update({"price_unit": self._get_discounted_price_unit()})
        return vals

    discount = fields.Float(string="Discount (%)", digits="Discount")

    # _sql_constraints = [
    #     (
    #         "discount_limit",
    #         "CHECK (discount <= 100.0)",
    #         "Discount must be lower than 100%.",
    #     )
    # ]

    def _get_discounted_price_unit(self):
        self.ensure_one()
        if self.discount:
            return self.price_unit * (1 - self.discount / 100)
        return self.price_unit

    @api.onchange("product_qty", "product_uom")
    def _onchange_quantity(self):
        res = super()._onchange_quantity()
        if self.product_id:
            date = None
            if self.order_id.date_order:
                date = self.order_id.date_order.date()
            seller = self.product_id._select_seller(
                partner_id=self.partner_id,
                quantity=self.product_qty,
                date=date,
                uom_id=self.product_uom,
            )
            self._apply_value_from_seller(seller)
        return res

    @api.model
    def _apply_value_from_seller(self, seller):
        if not seller:
            return

        for line in self:
            if seller.vendor_pricelist_id:
                product = line.product_id.with_context(
                    partner=self.partner_id,
                    quantity=line.product_uom_qty,
                    date=self.date_order,
                    pricelist=seller.vendor_pricelist_id.id,
                    uom=line.product_uom.id,
                    seller=seller,
                )
                try:
                    discount = max(0, (line.price_unit - product.vendor_price) * 100 / line.price_unit)
                    line.discount = discount
                except:
                    line.discount = 0

    def _prepare_account_move_line(self, move=False):
        vals = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        vals["discount"] = self.discount
        return vals

    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values, po):
        res = super(PurchaseOrderLine, self)._prepare_purchase_order_line_from_procurement(
                product_id, product_qty, product_uom, company_id, values, po)

        seller = product_id.with_company(company_id)._select_seller(
            partner_id=po.partner_id,
            quantity=product_qty,
            date=po.date_order and po.date_order.date(),
            uom_id=product_id.uom_po_id,
        )

        if seller.vendor_pricelist_id:
            product = product_id.with_context(
                    partner=po.partner_id,
                    quantity=product_qty,
                    date=po.date_order,
                    pricelist=seller.vendor_pricelist_id.id,
                    uom=product_uom.id,
                    seller=seller,
                )
            try:
                discount = max(0, (res.get('price_unit') - product.vendor_price) * 100 / res.get('price_unit'))

                res['discount'] = discount
            except:
                res['discount'] = 0
        return res

    # @api.model
    # def _prepare_purchase_order_line(
    #     self, product_id, product_qty, product_uom, company_id, supplier, po
    # ):
    #     res = super()._prepare_purchase_order_line(
    #         product_id, product_qty, product_uom, company_id, supplier, po
    #     )
    #     partner = supplier.name
    #     uom_po_qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id)
    #     seller = product_id.with_company(company_id)._select_seller(
    #         partner_id=partner,
    #         quantity=uom_po_qty,
    #         date=po.date_order and po.date_order.date(),
    #         uom_id=product_id.uom_po_id,
    #     )
    #     res.update(self._prepare_purchase_order_line_from_seller(seller))
    #     return res

    # @api.model
    # def _prepare_purchase_order_line_from_seller(self, seller):
    #     """Overload this function to prepare other data from seller,
    #     like in purchase_triple_discount module"""
    #     if not seller:
    #         return {}
    #     return {"discount": seller.discount}