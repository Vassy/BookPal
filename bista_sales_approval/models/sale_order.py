# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2022 (https://www.bistasolutions.com)
#
##############################################################################

from odoo import api, models, fields

AddState = [
    ("customer_approved", "Customer Approved"),
    ("min_price_review", "Price Review"),
    ("pending_for_approval", "Pending for Approval"),
    ("sale",),
]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(selection_add=AddState)
    sale_approval_log_ids = fields.One2many(
        "sale.approval.log", "sale_id", string="Approval Status"
    )
    product_price_check = fields.Boolean(string="Is product price approved?")

    def write(self, vals):
        if vals.get("state") and vals.get("state") == "draft":
            vals.update({"product_price_check": False})
        result = super(SaleOrder, self).write(vals)
        if vals.get("state") and vals.get("state") == "sent":
            self._create_sale_approval_log(
                self._context.get("uid"), "Quote Sent to Customer"
            )
        return result

    def action_approve_minimum_price(self):
        for rec in self:
            rec.product_price_check = True
            rec._create_sale_approval_log(self._context.get("uid"), "Price Approved")
            action = rec.action_send_for_approval()
            if action:
                return action

    def action_send_for_approval(self):
        for rec in self:
            order_lines = rec.order_line.filtered(
                lambda line: line.price_unit < line.product_id.minimum_sale_price
            ).ids
            if not rec.product_price_check and order_lines:
                return {
                    "name": "Confirmation",
                    "view_mode": "form",
                    "res_model": "min.price.wiz",
                    "type": "ir.actions.act_window",
                    "context": {
                        "default_sale_id": self.id,
                        "default_order_line_ids": order_lines,
                        "minimum_price": False,
                    },
                    "target": "new",
                }

            rec.state = "pending_for_approval"
            rec._create_sale_approval_log(
                self._context.get("uid"), "Quote Sent for Approval"
            )

    def action_approval(self):
        for rec in self:
            rec.action_confirm()
            rec._create_sale_approval_log(self._context.get("uid"), "Approved")

    def action_reject(self):
        return {
            "name": "Reject Reason",
            "view_mode": "form",
            "res_model": "reject.reason.wiz",
            "type": "ir.actions.act_window",
            "context": {"default_sale_id": self.id},
            "target": "new",
        }

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        self._create_sale_approval_log(self._context.get("uid"), "Cancelled")
        return res

    @api.model
    def create(self, values):
        res = super(SaleOrder, self).create(values)
        res._create_sale_approval_log(res.create_uid.id, "Quote Created")
        return res

    def _create_sale_approval_log(self, create_id, action):
        self.env["sale.approval.log"].create(
            {
                "sale_id": self.id,
                "action_user_id": create_id,
                "done_action": action,
                "action_date": fields.Datetime.now(),
            }
        )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    minimum_sale_price = fields.Float(related="product_id.minimum_sale_price")
    check_price_over_minimum = fields.Boolean(
        "Check if Price Below Min", compute="_check_price_over_minimum"
    )

    def _check_price_over_minimum(self):
        for rec in self:
            if (
                rec.minimum_sale_price > rec.price_unit
                and rec.order_id.state == "min_price_review"
            ):
                rec.check_price_over_minimum = True
            else:
                rec.check_price_over_minimum = False


class SaleApprovalLog(models.Model):
    _name = "sale.approval.log"
    _description = "Log information of Sale Order Approval Process"

    sale_id = fields.Many2one("sale.order")
    note = fields.Text(string="Reason")
    done_action = fields.Char(string="Performed Action")
    action_user_id = fields.Many2one("res.users", string="User")
    action_date = fields.Datetime(string="Date")
