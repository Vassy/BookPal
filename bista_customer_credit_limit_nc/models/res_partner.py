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

    @api.constrains("check_over_credit", "credit_limit")
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
                lines = sale.order_line.filtered(
                    lambda line: line.invoice_status != "invoiced"
                )
                if not open_invoice and not lines:
                    continue
                amount_total = sum(sale.order_line.mapped("price_total"))
                payments = sale.invoice_ids.filtered(
                    lambda inv: inv.payment_state in ["in_payment", "paid", "partial"]
                )._get_reconciled_payments()
                paid_payment = payments.filtered(lambda p: p.is_matched)
                amount += amount_total - sum(paid_payment.mapped("amount_signed"))
            partner.available_credit_limit = partner.credit_limit - amount
