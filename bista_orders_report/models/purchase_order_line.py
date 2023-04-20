
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"
    _description = "Purchase Order Line Description"

    origin = fields.Char(related="order_id.origin")
    date_approve = fields.Datetime(related="order_id.date_approve")
    uom_id = fields.Many2one(related="product_id.uom_id", string="UOM")
    qty_remain_receive = fields.Float(
        "Remaining Qty", compute="compute_remain_qty")
    qty_remain_receive_value = fields.Float(
        "Remaining Value", compute="compute_remain_qty")
    qty_shortclose = fields.Float(
        'Return/Short Close Qty', compute="compute_remain_qty")
    short_close_price = fields.Float(
        compute="compute_remain_qty", string="Return/Short Close Value")
    qty_received_uom = fields.Float(compute="compute_remain_qty")
    qty_received_value = fields.Float(
        compute="compute_remain_qty",
        string="Received Value")
    line_status = fields.Selection(
        [('purchase', 'Purchase Order'),
         ('received', 'Received'),
         ('short_close', 'Short Closed'),
         ('partial_received', 'Partially Received')],
        'PO Line Status',
        compute="_cal_line_status", store=True)
    invoice_status = fields.Selection(related="order_id.invoice_status")
    industry_id = fields.Many2one('res.partner.industry',
                                    related="partner_id.industry_id",
                                    store=True)

    @api.depends('qty_received', 'qty_shortclose', 'qty_remain_receive')
    def _cal_line_status(self):
        for line in self:
            if line.qty_received and line.qty_received == line.product_uom_qty:
                line.line_status = 'received'
            elif line.qty_shortclose:
                line.line_status = 'short_close'
            elif line.qty_remain_receive:
                line.line_status = 'partial_received'
            else:
                line.line_status = 'purchase'

    def compute_remain_qty(self):
        """Calculate remain and short close qty."""
        for line in self:
            line.qty_remain_receive = 0
            line.qty_shortclose = 0
            line.qty_received_uom = line.product_uom._compute_quantity(
                line.qty_received, line.uom_id)

            line.qty_received_value = line.qty_received_uom * line.price_unit
            line.short_close_price = 0
            line.qty_remain_receive_value = 0
            if line.qty_received_uom != \
                    line.product_uom_qty:
                if line.move_ids.filtered(
                    lambda x: x.state not in ['done', 'cancel']) or \
                    line.move_dest_ids.filtered(
                        lambda x: x.state not in ['done', 'cancel']):
                    line.qty_remain_receive = line.product_uom_qty - \
                        line.qty_received_uom
                    line.qty_remain_receive_value = line.qty_remain_receive * \
                        line.price_unit
                else:
                    line.qty_shortclose = line.product_uom_qty - \
                        line.qty_received_uom
                    line.short_close_price = line.qty_shortclose * \
                        line.price_unit
