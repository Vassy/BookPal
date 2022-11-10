
from odoo import api, fields, models
import datetime


class PurchaseOrderReportWiz(models.TransientModel):
    _name = 'purchase.order.status.report.wiz'
    _description = 'Purchase Order Report Wizard'

    from_date = fields.Date(
        string="From Date",
        default=datetime.datetime.today().replace(day=1))
    to_date = fields.Date(
        string="To Date", default=fields.Date.context_today)
    product_ids = fields.Many2many('product.product', string="Products")
    supplier_ids = fields.Many2many(
        'res.partner', string='Vendors',
        domain="[('supplier_rank', '>', 0)]")
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')

    def generate_purchase_order_status(self):
        """Based on configuration generate the PO status report."""
        if self.from_date and self.to_date:
            from_date = str(self.from_date) + ' ' + str(
                datetime.timedelta(hours=0, minutes=0, seconds=0))
            to_date = str(self.to_date) + ' ' + str(
                datetime.timedelta(hours=23, minutes=59, seconds=59))
            domain = [('display_type', '=', False),
                      ('product_id.detailed_type', 'in',
                       ['consu', 'product']),
                      ('date_order', '>=', from_date),
                      ('date_order', '<=', to_date),
                      ('order_id.state', 'not in', ['draft', 'cancel'])]
            if self.product_ids:
                domain.append(
                    ('product_id', 'in', self.product_ids.ids))
            if self.warehouse_id:
                domain.append(
                    ('order_id.warehouse_id', '=', self.warehouse_id.id))
            if self.supplier_ids:
                domain.append(
                    ('order_id.partner_id', 'in', self.supplier_ids.ids))

            # report_name = "Purchase Order Status Report"
            action = self.env.ref(
                'bista_orders_report.'
                'action_purchase_order_line_status').read()[0]
            action.update({'domain': domain})
            return action


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    origin = fields.Char(related="order_id.origin")
    warehouse_id = fields.Many2one(related="order_id.warehouse_id")
    uom_id = fields.Many2one(related="product_id.uom_id")
    qty_remain_receive = fields.Float(
        "Remaining Qty", compute="compute_remain_qty")
    qty_remain_receive_value = fields.Float(
        "Remaining Value", compute="compute_remain_qty")
    qty_shortclose = fields.Float(
        'Short Close Qty', compute="compute_remain_qty")
    short_close_price = fields.Float(
        compute="compute_remain_qty", string="Short Close Value")
    qty_received_uom = fields.Float(
        compute="compute_remain_qty",
        string="Received Qty")
    qty_received_value = fields.Float(
        compute="compute_remain_qty",
        string="Received Value")
    line_status = fields.Selection(
        [('purchase', 'Purchase Order'),
         ('received', 'Received'),
         ('short_close', 'Short Closed'),
         ('partial_received', 'Partially Received')],
        'Line Status',
        compute="_cal_line_status", store=True)

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
            if line.qty_received_uom and line.qty_received_uom != \
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
