# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    pricelist_id = fields.Many2one(
        "product.pricelist",
        "Pricelist",
        compute="_compute_product_pricelist",
        store=True,
    )
    without_disc_amount_untaxed = fields.Monetary(
        string="Amount Untaxed (Without Disc.)", store=True, compute="_amount_all"
    )
    total_discount_amount = fields.Monetary(
        string="Discount", store=True, compute="_amount_all"
    )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for line in self.order_line:
            line._onchange_quantity()

    @api.onchange("currency_id")
    def onchange_currency_pricelist(self):
        if self.pricelist_id.currency_id != self.currency_id:
            self.pricelist_id = False

    def _amount_all(self):
        super(PurchaseOrder, self)._amount_all()
        for order in self:
            without_disc_amount_untaxed = total_discount_amount = 0.0
            for line in order.order_line:
                without_disc_amount_untaxed += line.without_disc_price_subtotal
                total_discount_amount += line.discount_amount
            currency = (
                order.currency_id
                or order.partner_id.property_purchase_currency_id
                or self.env.company.currency_id
            )
            order_data = {
                "without_disc_amount_untaxed": currency.round(
                    without_disc_amount_untaxed
                ),
                "total_discount_amount": currency.round(total_discount_amount),
            }
            order.update(order_data)

    @api.depends("partner_id")
    def _compute_product_pricelist(self):
        for order in self:
            order.pricelist_id = order.partner_id.property_product_vendor_pricelist

    def update_prices(self):
        for order in self.filtered(lambda o: o.pricelist_id):
            pricelist_line = order.pricelist_id.get_pricelist_line_based_on_order(
                order.without_disc_amount_untaxed,
                sum(order.order_line.mapped("product_qty")),
            )
            non_discounted_lines = order.order_line
            if non_discounted_lines and pricelist_line:
                non_discounted_lines.discount = pricelist_line.discount
            else:
                non_discounted_lines.discount = 0


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    pricelist_id = fields.Many2one("product.pricelist", "Pricelist")
    before_disc_price_unit = fields.Float(string="Cover Price", digits="Product Price")
    discount = fields.Float(string="Discount (%)", digits="Discount")
    without_disc_price_subtotal = fields.Monetary(
        compute="_compute_amount", string="Without Disc. Subtotal", store=True
    )
    discount_amount = fields.Monetary(
        compute="_compute_amount", string="Discount Amount", store=True
    )
    price_unit = fields.Float(compute="_compute_disc_price_unit", store=True)

    @api.depends("before_disc_price_unit", "discount")
    def _compute_disc_price_unit(self):
        for order_line in self:
            order_line.price_unit = order_line._get_discounted_price_unit()

    # adding discount to depends
    @api.depends("discount")
    def _compute_amount(self):
        res = super()._compute_amount()
        for line in self:
            vals = line._prepare_compute_all_values()
            vals.update({"price_unit": line.before_disc_price_unit})
            taxes = line.taxes_id.compute_all(**vals)
            line_data = {
                "discount_amount": taxes["total_excluded"] - line.price_subtotal,
                "without_disc_price_subtotal": taxes["total_excluded"],
            }
            line.update(line_data)
        return res

    def _prepare_compute_all_values(self):
        vals = super()._prepare_compute_all_values()
        vals.update({"price_unit": self._get_discounted_price_unit()})
        return vals

    def _get_discounted_price_unit(self):
        self.ensure_one()

        if self.discount:
            return self.before_disc_price_unit * (1 - self.discount / 100)
        return self.before_disc_price_unit

    @api.onchange("product_qty", "product_uom")
    def _onchange_quantity(self):
        super()._onchange_quantity()
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

    def _apply_value_from_seller(self, seller):
        self.before_disc_price_unit = self.price_unit
        if not seller.vendor_pricelist_id:
            self.discount = 0
            return

        self.pricelist_id = seller.vendor_pricelist_id.id
        product_context = dict(
            self.env.context,
            partner_id=self.order_id.partner_id.id,
            date=self.order_id.date_order,
            uom=self.product_uom.id,
        )
        price, rule_id = self.pricelist_id.with_context(
            product_context
        ).get_product_price_rule(
            self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id
        )
        discount = 0
        if rule_id:
            rule = self.env["product.pricelist.item"].browse(rule_id)
            price = rule._compute_price(
                seller.price, self.product_uom, self.product_id, self.product_uom_qty
            )
            if self.pricelist_id.discount_policy == "with_discount":
                self.before_disc_price_unit = price
            else:
                discount = max(0, (seller.price - price) * 100 / seller.price)
        self.discount = discount
        self._compute_disc_price_unit()

    def _prepare_account_move_line(self, move=False):
        vals = super()._prepare_account_move_line(move)
        vals["discount"] = self.discount
        vals["price_unit"] = self.before_disc_price_unit
        return vals

    @api.model
    def _prepare_purchase_order_line_from_procurement(
        self, product_id, product_qty, product_uom, company_id, values, po
    ):
        res = super()._prepare_purchase_order_line_from_procurement(
            product_id, product_qty, product_uom, company_id, values, po
        )
        res["before_disc_price_unit"] = res.get("price_unit")
        seller = product_id.with_company(company_id)._select_seller(
            partner_id=po.partner_id,
            quantity=product_qty,
            date=po.date_order and po.date_order.date(),
            uom_id=product_id.uom_po_id,
        )
        if not seller.vendor_pricelist_id:
            return res

        res["pricelist_id"] = seller.vendor_pricelist_id.id
        product_context = dict(
            self.env.context,
            partner_id=po.partner_id.id,
            date=po.date_order,
            uom=product_uom.id,
        )
        price, rule_id = seller.vendor_pricelist_id.with_context(
            product_context
        ).get_product_price_rule(product_id, product_qty or 1.0, po.partner_id)
        if rule_id:
            rule = self.env["product.pricelist.item"].browse(rule_id)
            price = rule._compute_price(
                seller.price, product_uom, product_id, product_uom
            )
            if seller.vendor_pricelist_id.discount_policy == "with_discount":
                res["before_disc_price_unit"] = price
            else:
                discount = max(
                    0, (res.get("price_unit") - price) * 100 / res.get("price_unit")
                )
                res["discount"] = discount
        return res
