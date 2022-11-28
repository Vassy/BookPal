# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    check_over_credit = fields.Boolean(string="Check Credit Limit?")
    available_credit_limit = fields.Monetary(
        compute="_compute_available_credit_limit",
        string="Available Limit",
        help="Available Credit limit for the Customer",
    )

    @api.constrains("check_over_credit", "available_credit_limit")
    def _check_credit_limit(self):
        for partner in self:
            if partner.check_over_credit and partner.credit_limit < 1:
                raise ValidationError(
                    _("Credit Limit should be greater than or equal to 1.")
                )

    def _compute_available_credit_limit(self):
        for partner in self:
            if not partner.check_over_credit:
                partner.available_credit_limit = 0.00
                continue
            sale_domain = [
                ("partner_id", "child_of", partner.ids),
                ("state", "=", "sale"),
            ]
            amount = 0
            for sale in self.env["sale.order"].search(sale_domain):
                open_invoice = sale.invoice_ids.filtered(
                    lambda inv: inv.payment_state != "paid"
                )
                deliver_lines = sale.picking_ids.filtered(
                    lambda p: p.state not in ["done", "cancel"]
                ) or sale.order_line.filtered(
                    lambda line: line.product_id.invoice_policy == "delivery"
                    and line.qty_delivered != line.qty_invoiced
                )
                product_lines = sale.order_line.filtered(
                    lambda line: line.product_id.invoice_policy == "order"
                    and line.product_uom_qty != line.qty_invoiced
                )
                if not open_invoice and not deliver_lines and not product_lines:
                    continue
                order_lines = sale.order_line.filtered(
                    lambda l: l.product_id.invoice_policy != "delivery"
                )
                amount_total = sum(order_lines.mapped("price_total"))
                for line in sale.order_line - order_lines:
                    open_moves = line.move_ids.filtered(
                        lambda m: m.state not in ["done", "cancel"]
                    )
                    if any(open_moves):
                        amount_total += line.price_total
                    else:
                        price_unit = line.price_total / line.product_uom_qty
                        amount_total += price_unit * line.qty_delivered
                paid_invoice = sale.invoice_ids.filtered(
                    lambda inv: inv.payment_state == "paid"
                ).mapped("amount_total_signed")
                amount += amount_total - sum(paid_invoice)
            partner.available_credit_limit = partner.credit_limit - amount
