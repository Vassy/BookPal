# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_cancel(self):
        # validation for multi step transfer which is depends on other transfer
        if any(
            "done" in move.move_dest_ids.mapped("state") and move.state == "done"
            for move in self
        ):
            msg = _(
                "Delivery Is Already done for this Picking. "
                "Cancel Delivery First and Then Picking."
            )
            raise ValidationError(msg)
        self.mapped("move_line_ids").write({"state": "draft", "qty_done": 0})
        self.write({"state": "draft"})
        for account in self.mapped("account_move_ids"):
            account.sudo().button_cancel()
            account.sudo().with_context(force_delete=True).unlink()
        return super()._action_cancel()
