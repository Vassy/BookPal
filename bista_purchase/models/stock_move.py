# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    def write(self, vals):
        res = super(StockMove, self).write(vals)
        # update po line status (shipment tracking)
        if vals.get('state') == 'done':
            received_status_id = self.env.ref('bista_purchase.status_line_received')
            partially_received_status_id = self.env.ref('bista_purchase.status_line_partially_received')
            stocked_status_id = self.env.ref('bista_purchase.status_line_stocked')
            input_location_id = self.env.ref('stock.stock_location_company')
            stock_location_id = self.env.ref('stock.stock_location_stock')
            for move in self:
                if move.state == 'done' and move.purchase_line_id and move.location_dest_id == input_location_id:
                    # purchase_quantity_received = self.purchase_line_id.qty_received + self.quantity_done
                    purchase_quantity_received = move.purchase_line_id.qty_received
                    move.purchase_line_id.status_id = received_status_id.id if move.purchase_line_id.product_qty == purchase_quantity_received else partially_received_status_id.id
                if move.state == 'done' and move.move_orig_ids.mapped('purchase_line_id') and move.location_dest_id == stock_location_id:
                    move.move_orig_ids.mapped('purchase_line_id').status_id = stocked_status_id.id
        return res
