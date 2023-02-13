# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    special_pick_note = fields.Html("Notes")

    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({"note": self.special_pick_note})
        return res

    @api.depends(
        "order_line.move_ids.picking_id",
        "order_line.move_ids.move_dest_ids.picking_id",
        "order_line.move_ids.move_dest_ids.returned_move_ids.picking_id",
    )
    def _compute_picking_ids(self):
        for order in self:
            pickings = order.order_line.move_ids.picking_id
            internal_moves = order.order_line.move_ids.mapped("move_dest_ids")
            pickings |= internal_moves.mapped("picking_id")
            return_moves = internal_moves.mapped("returned_move_ids")
            pickings |= return_moves.mapped("picking_id")
            order.picking_ids = pickings

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for order in self:
            pickings = self.env["stock.picking"]
            for line in order.order_line:
                moves = line.move_ids
                pickings |= moves.mapped("picking_id")
            for picking in pickings:
                for move in picking.move_ids_without_package.filtered(
                    lambda s: s.move_dest_ids
                ):
                    move.move_dest_ids.picking_note = move.picking_note
                    move.move_dest_ids.picking_id.note = move.picking_id.note
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    receipt_note = fields.Char("Remarks")

    def _prepare_stock_move_vals(
        self, picking, price_unit, product_uom_qty, product_uom
    ):
        res = super()._prepare_stock_move_vals(
            picking, price_unit, product_uom_qty, product_uom
        )
        res.update({"picking_note": self.receipt_note})
        return res
