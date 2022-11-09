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
            for move in self:
                if move.state == 'done' and move.purchase_line_id:
                    # purchase_quantity_received = self.purchase_line_id.qty_received + self.quantity_done
                    purchase_quantity_received = move.purchase_line_id.qty_received
                    move.purchase_line_id.status_id = received_status_id.id if move.purchase_line_id.product_qty == purchase_quantity_received else partially_received_status_id.id
        return res
