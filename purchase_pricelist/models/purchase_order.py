# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    pricelist_id = fields.Many2one('product.pricelist', "Pricelist", compute="_compute_product_pricelist", store=True)
    without_disc_amount_untaxed = fields.Monetary(string='Without Untaxed Amount', store=True, readonly=True, compute='_amount_all')
    total_discount_amount = fields.Monetary(string='Total Discount Amount', store=True, readonly=True, compute='_amount_all')
    total_quantity = fields.Float(string="Total Quantity", store=True, compute="_compute_total_quantity")

    @api.depends('order_line', 'order_line.product_qty')
    def _compute_total_quantity(self):
        for order in self:
            order.total_quantity = sum(order.order_line.mapped('product_qty'))

    @api.onchange('currency_id')
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
            currency = order.currency_id or order.partner_id.property_purchase_currency_id or self.env.company.currency_id
            order.update({
                'without_disc_amount_untaxed': currency.round(without_disc_amount_untaxed),
                'total_discount_amount': currency.round(total_discount_amount),
            })

    @api.depends('partner_id')
    def _compute_product_pricelist(self):
        for order in self:
            order.pricelist_id = order.partner_id.property_product_vendor_pricelist

    def update_prices(self):
        for order in self:
            if order.pricelist_id:
                price_list_line = order.pricelist_id.get_pricelist_order_line_based_on_order(order.without_disc_amount_untaxed, order.total_quantity)
                non_discounted_lines = order.order_line
                if non_discounted_lines and price_list_line:
                    non_discounted_lines.discount = price_list_line.discount
                else:
                    non_discounted_lines.discount = 0


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    disc_price_unit = fields.Float(string="Disc Unit Price", compute="_compute_disc_price_unit")
    without_disc_price_subtotal = fields.Monetary(compute='_compute_amount', string='Without Disc. Subtotal', store=True)
    discount_amount = fields.Monetary(compute='_compute_amount', string='Discount Amount', store=True)

    def _compute_disc_price_unit(self):
        for order_line in self:
            order_line.disc_price_unit = order_line._get_discounted_price_unit()

    # adding discount to depends
    @api.depends("discount")
    def _compute_amount(self):
        res = super()._compute_amount()
        for line in self:
            vals = line._prepare_compute_all_values()
            vals.update({'price_unit': line.price_unit})
            taxes = line.taxes_id.compute_all(**vals)
            line.update({
                # 'price_tax': taxes['total_included'] - taxes['total_excluded'],
                # 'price_total': taxes['total_included'],
                'discount_amount': line.price_subtotal - taxes['total_excluded'],
                'without_disc_price_subtotal': taxes['total_excluded'],
            })
        return res

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
            for line in self:
                line.discount = 0
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
                    vendor_price = seller.currency_id._convert(product.vendor_price, line.order_id.currency_id, line.order_id.company_id, fields.Date.today())
                    discount = max(0, (line.price_unit - vendor_price) * 100 / line.price_unit)
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
