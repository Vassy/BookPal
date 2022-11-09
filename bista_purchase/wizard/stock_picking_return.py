# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        new_picking_id, picking_type_id = super(ReturnPicking, self)._create_returns()
        # update po line status while creating return
        if new_picking_id:
            return_picking = self.env['stock.picking'].browse(new_picking_id)
            input_location_id = self.env.ref('stock.stock_location_company')
            vendor_location_id = self.env.ref('stock.stock_location_suppliers')
            if return_picking.location_dest_id == vendor_location_id and return_picking.location_id == input_location_id:
                return_created_status_id = self.env.ref('bista_purchase.status_line_return')
                return_picking.move_lines.move_orig_ids.mapped('purchase_line_id').status_id = return_created_status_id.id
        return new_picking_id, picking_type_id
