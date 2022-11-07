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
            for rec in values:
                pick = rec['ship_line']
                if pick:
                    pick_note = {
                        'picking_note': pick.picking_note
                        }
                rec.update(pick_note)
        elif values and type(values) is dict:
            values.update(pick_note)
        return values


class SaleMultiShipQtyLines(models.Model):
    _inherit = "sale.multi.ship.qty.lines"
    _description = 'Sale Multi Ship Qty Lines model details.'


    picking_note = fields.Text('Picking Note')

    @api.onchange('so_line_id')
    def onchange_product_vendor(self):
        if self.so_line_id:
            self.picking_note = self.so_line_id.picking_note