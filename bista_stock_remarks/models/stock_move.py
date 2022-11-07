# -*- coding: utf-8 -*-
from odoo import  _,api,fields, models

class StockMove(models.Model):
    _inherit = "stock.move"

    picking_note = fields.Char(string="Picking Note", copy=False)

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields.append('picking_note')
        return distinct_fields

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        if self.group_id.sale_id.common_pick_note:
            vals['note'] = self.group_id.sale_id.common_pick_note
        else:
            purchase_id = self.env['purchase.order'].search([('name', '=', vals['origin'])])
            if purchase_id and purchase_id.special_pick_note:
                vals['note'] = purchase_id.special_pick_note
        return vals

