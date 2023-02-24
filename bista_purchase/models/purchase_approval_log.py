# -*- coding: utf-8 -*-

from odoo import models, fields


class PurchaseApprovalLog(models.Model):
    _name = "purchase.approval.log"
    _description = "Log information of Purchase Order Approval Process"

    order_id = fields.Many2one("purchase.order", ondelete="cascade")
    note = fields.Text(string="Reason")
    done_action = fields.Char(string="Performed Action")
    action_user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.uid
    )
    action_date = fields.Datetime(string="Date", default=fields.Datetime.now)
    old_state = fields.Char(string="Old State")
    state = fields.Char(string="State")
