# -*- coding: utf-8 -*-

from odoo import api, models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def create(self, vals):
        """Remove fiscal position.

        Make blank fiscal position if invoce create from
        bigcommerce order.
        """
        if self._context.get("active_model") == "sale.order":
            sale_order_id = self.env["sale.order"].browse(
                self._context.get("active_id")
            )
            if sale_order_id.big_commerce_order_id:
                vals.update({"fiscal_position_id": False})
        return super(AccountMove, self).create(vals)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_format = fields.Char(related="product_id.product_format")
