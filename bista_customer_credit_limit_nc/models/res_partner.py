# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    check_over_credit = fields.Boolean(string="Check Credit Limit?")
    available_credit_limit = fields.Monetary(
        compute="_compute_available_credit_limit",
        string="Available Limit",
        help="Available Credit limit for the Customer",
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
                paid_invoice = sale.invoice_ids.filtered(
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
                if not paid_invoice and not deliver_lines and not product_lines:
                    continue
                amount += sale.amount_total - sum(
                    sale.invoice_ids.filtered(
                        lambda inv: inv.payment_state == "paid"
                    ).mapped("amount_total_signed")
                )
            partner.available_credit_limit = partner.credit_limit - amount
