# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_cancel(self):
        # validation for multi step transfer which is depends on other transfer
        for move in self.filtered(lambda m: m.state == "done"):
            if "done" in move.move_dest_ids.mapped("state"):
                msg = _(
                    "You need to cancel first '%s', Then you can cancel this transfer."
                    % ", ".join(move.move_dest_ids.mapped("picking_id.name"))
                )
                raise ValidationError(msg)
        self.mapped("move_line_ids").write({"state": "draft", "qty_done": 0})
        self.write({"state": "draft"})
        for account in self.mapped("account_move_ids"):
            account.sudo().button_cancel()
            account.sudo().with_context(force_delete=True).unlink()
        return super()._action_cancel()
