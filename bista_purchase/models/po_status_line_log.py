# -*- coding: utf-8 -*-

from odoo import models, fields


class PoStatusLineLog(models.Model):
    _name = "po.status.line.log"
    _description = "Log information of po status line"

    po_line_id = fields.Many2one("purchase.order.line", ondelete="cascade")
    # next_followup_date = fields.Date("Next Followup Date", copy=False)
    note = fields.Text("Notes", copy=False)
    action_user_id = fields.Many2one(
        "res.users", string="Updated By", default=lambda self: self.env.uid
    )
    action_date = fields.Datetime(string="Date", default=fields.Datetime.now)
    status_id = fields.Many2one("po.status.line", string="Line Status")
