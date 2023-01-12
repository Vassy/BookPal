# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    special_pick_note = fields.Html('Notes')

    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({'note': self.special_pick_note})
        return res

    @api.depends('order_line.move_ids.returned_move_ids',
                 'order_line.move_ids.state',
                 'order_line.move_ids.picking_id')
    def _compute_picking_ids(self):
        for order in self:
            pickings = self.env['stock.picking']
            picking_obj = self.env['stock.picking']
            pick = None
            for line in order.order_line:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.move_ids | line.move_ids.mapped('returned_move_ids')
                pickings |= moves.mapped('picking_id')
            if pickings:
                for picking in pickings:
                    internal_pickings = picking_obj.search(
                        [('origin', 'in', (picking.name, order.name))])
                    if internal_pickings:
                        pickings |= internal_pickings
                    # fetch the return of internal transfer
                    for int_pick in internal_pickings:
                        if int_pick.move_lines.mapped('returned_move_ids'):
                            return_internal_pick = picking_obj.search(
                                [('origin', 'ilike', int_pick.name)])
                            if return_internal_pick:
                                pickings |= return_internal_pick
                    if picking.move_ids_without_package:
                        for move in picking.move_ids_without_package.filtered(
                                lambda s: s.move_dest_ids):
                            pickings |= move.move_dest_ids.mapped('picking_id')
            order.picking_ids = pickings

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for order in self:
            pickings = self.env['stock.picking']
            for line in order.order_line:
                moves = line.move_ids 
                pickings |= moves.mapped('picking_id')
            if pickings:
                for picking in pickings:
                    if picking.move_ids_without_package:
                        for move in picking.move_ids_without_package.filtered(
                                lambda s: s.move_dest_ids):
                            move.move_dest_ids.picking_note = move.picking_note 
                            move.move_dest_ids.picking_id.note = move.picking_id.note
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    receipt_note = fields.Char('Remarks')

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super(PurchaseOrderLine, self)._prepare_stock_move_vals\
            (picking, price_unit, product_uom_qty, product_uom)
        res.update({'picking_note': self.receipt_note})
        return res
