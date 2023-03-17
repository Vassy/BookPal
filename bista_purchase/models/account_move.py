# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_pick_note = fields.Html("Common Notes")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    bp_price = fields.Float("BP Price", compute="_compute_discount_price", store=True)
    quote_price = fields.Float(
        "Quote Price", compute="_compute_discount_price", store=True
    )

    @api.depends("price_unit", "discount")
    def _compute_discount_price(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.currency_id:
                line.bp_price = line.currency_id.round(price)
                line.quote_price = line.currency_id.round(price)

    def create(self, vals):
        res = super(AccountMoveLine, self).create(vals)
        for move_line in res:
            invoiced_status_id = self.env.ref("bista_purchase.status_line_invoiced")
            move_line.purchase_line_id.status_id = invoiced_status_id.id
        return res

    def _get_price_total_and_subtotal(
        self,
        price_unit=None,
        quantity=None,
        discount=None,
        currency=None,
        product=None,
        partner=None,
        taxes=None,
        move_type=None,
    ):
        price_unit = self.price_unit if price_unit is None else price_unit
        if not self._context.get('create_bill') and price_unit:
            discount = 100 - (self.quote_price / price_unit * 100)
        result = super()._get_price_total_and_subtotal(
            price_unit, quantity, discount, currency, product, partner, taxes, move_type
        )
        return result
