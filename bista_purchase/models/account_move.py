# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_pick_note = fields.Html("Common Notes")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    bp_price = fields.Float("BP Price", compute="_compute_discount_price")
    quote_price = fields.Float("Quote Price", compute="_compute_discount_price")

    def _compute_discount_price(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line.bp_price = int(price * 10**3) / 10**3
            line.quote_price = int(price * 10**3) / 10**3

    def create(self, vals):
        res = super(AccountMoveLine, self).create(vals)
        for move_line in res:
            invoiced_status_id = self.env.ref("bista_purchase.status_line_invoiced")
            move_line.purchase_line_id.status_id = invoiced_status_id.id
        return res
