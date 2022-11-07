# -*- coding: utf-8 -*-
from odoo import  _,api,fields, models



class SaleOrder(models.Model):
    _inherit = "sale.order"

    common_pick_note = fields.Html('Common Notes',)



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    picking_note = fields.Text('Picking Note')

    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        pick_note = {
            'picking_note': self.picking_note
            }
        if values and type(values) is list:
            values[0].update(pick_note)
        elif values and type(values) is dict:
            values.update(pick_note)
        return values
