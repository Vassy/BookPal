# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_order_id = fields.Many2one(
        "sale.order", "Sale Ref.", copy=False, help="Sale Order Reference"
    )
    state = fields.Selection(
        selection_add=[("credit_review", "Credit Review")],
        ondelete={"credit_review": "cascade"},
        help="Invoice State",
    )
    inv_confirm_check = fields.Boolean(
        compute="get_inv_check_confirm", string="Is credit limit Over?"
    )
    credit_review_ids = fields.One2many(
        "credit.review.log",
        "invoice_order_id",
        "Credit Review Log",
        help="Invoice Credit Review",
    )

    def action_credit_review(self):
        for account_move in self:
            account_move.state = "credit_review"

    @api.depends("partner_id", "invoice_line_ids")
    def get_inv_check_confirm(self):
        for inv in self:
            inv.inv_confirm_check = False
            if (
                inv.partner_id.check_over_credit
                and inv.move_type in ["out_invoice", "out_receipt"]
                and not inv.sale_order_id
                and inv.partner_id.available_credit_limit - inv.amount_total < 0
            ):
                inv.inv_confirm_check = True

    def action_invoice_open(self):
        for inv in self:
            if self.env.context.get("review_log", False):
                self.env["credit.review.log"].generate_credit_review_log(
                    user=inv.write_uid.id,
                    date=inv.write_date,
                    sale_id=False,
                    inv_id=inv.id,
                )
                inv.state = "draft"
        return super(AccountMove, self).action_post()
