# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2022 (https://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class SaleOrderRejectReason(models.TransientModel):
    _name = "reject.reason.wiz"
    _description = "Reason for Rejection"

    sale_id = fields.Many2one("sale.order", ondelete="cascade")
    note = fields.Text(string="Reason for rejection", required=True)

    def update_reject_reason(self):
        state = "order_booked"
        if self.sale_id.state == "quote_approval":
            state = "draft"
        self.sale_id.write({"state": state})
        log_data = {
            "sale_id": self.sale_id.id,
            "done_action": "Quote Rejected",
            "note": self.note,
        }
        self.env["sale.approval.log"].create(log_data)
