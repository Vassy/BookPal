
from odoo import api, _, fields, models

class StockPicking(models.Model):
    _inherit = "stock.picking"


    def _create_backorder(self):
        res = super(StockPicking, self)._create_backorder()
        for back_picking in res.move_ids_without_package:
            for picking in self.move_ids_without_package:
                if back_picking.product_id.id == picking.product_id.id:
                    back_picking.picking_note = picking.picking_note
        return res

    def get_po_ref_from_transfer(self):
        name = ''
        vals = {}
        po = self.move_ids_without_package.mapped('move_orig_ids').mapped('purchase_line_id')
        if po:
            for rec in po:
                if rec.order_id.name not in name:
                    name += rec.order_id.name + ', '
        vals.update({
            'name': name[:-2],
            'vendor_id': po.order_id.partner_id

        })
        return vals