# -*- coding: utf-8 -*-
from odoo import  _,api,fields, models

class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += ['picking_note']
        return fields

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id,
                               values):
        move_values = super()._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin,
                                                     company_id, values)
        move_dest_ids = values.get('move_dest_ids', False)
        if values.get('move_dest_ids', False):
            notes = move_dest_ids.picking_note
            if notes:
                move_values.update({
                    'picking_note': notes,
                })
        return move_values
