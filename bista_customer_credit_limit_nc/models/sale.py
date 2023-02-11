# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    confirm_check = fields.Boolean(
        compute="get_check_confirm", string="Is credit limit Over?"
    )
    state = fields.Selection(
        selection_add=[("credit_review", "Credit Review"), ("sale",)]
    )
    available_credit_limit = fields.Monetary(
        related="partner_id.available_credit_limit"
    )

    def trigger_order_action(self):
        action = super().trigger_order_action()
        if self.env.user.has_group("bista_customer_credit_limit_nc.group_credit_limit"):
            action["context"].update({"search_default_credit_review": 1})
            if (
                "search_default_order_approval" in action["context"]
                or "search_default_booked_order" in action["context"]
            ):
                action["context"].update({"search_default_groupby_state": 1})
        return action

    def action_override_and_send_for_approve(self):
        for rec in self:
            rec._create_sale_approval_log("Overriden Credit Limit")
            action = rec.action_send_for_approval()
            if action:
                return action

    def get_check_confirm(self):
        for sale in self:
            sale.confirm_check = False
            if not sale.partner_id.check_over_credit:
                continue
            if sale.available_credit_limit - sale.amount_total < 0:
                sale.confirm_check = True

    def action_check_credit_for_approval(self):
        for sale in self:
            sale.state = "credit_review"
            sale._create_sale_approval_log(
                "Quote send for Review for Credit Limit Overriding"
            )

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if res:
            res.update({"sale_order_id": self.id})
        return res


class CreditReviewLog(models.Model):
    _name = "credit.review.log"
    rec_name = "review_user_id"
    _description = "Credit Review Logs"

    review_user_id = fields.Many2one("res.users", "Credit Review By", readonly=True)
    review_date = fields.Datetime(string="Credit Review Date", readonly=True)
    sale_order_id = fields.Many2one("sale.order", "Sale Order Ref")
    invoice_order_id = fields.Many2one("account.move", "Invoice Ref")

    def generate_credit_review_log(self, user, date, sale_id=False, inv_id=False):
        return self.create(
            {
                "review_user_id": user,
                "review_date": date,
                "sale_order_id": sale_id,
                "invoice_order_id": inv_id,
            }
        )
