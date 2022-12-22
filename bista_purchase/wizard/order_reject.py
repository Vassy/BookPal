# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2022 (https://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class OrderRejectReason(models.TransientModel):
    _name = "order.reject.wiz"
    _description = "Order Rejection"

    order_id = fields.Many2one("purchase.order", ondelete="cascade")
    note = fields.Text(string="Reason for rejection")

    def action_reject_reason(self):
        log_data = {
            "order_id": self.order_id.id,
            "done_action": "RFQ Rejected",
            "note": self.note,
            "old_state": self.order_id.state,
            "state": "reject"
        }
        self.env["purchase.approval.log"].create(log_data)
        self.order_id.with_context(no_history_update=True).write({
                    "state": "reject",
                })
