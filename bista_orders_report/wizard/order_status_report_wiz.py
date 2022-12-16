
from odoo import fields, models, _
import datetime


class SaleOrderReportWiz(models.TransientModel):
    _name = 'order.status.report.wiz'
    _description = 'Sale Order Report Wizard'

    from_date = fields.Date(
        string="From Date",
        default=datetime.datetime.today().replace(day=1))
    to_date = fields.Date(
        string="To Date", default=fields.Date.context_today)
    product_ids = fields.Many2many('product.product', string="Products")
    supplier_ids = fields.Many2many(
        'res.partner', string='Vendors',
        domain="[('supplier_rank', '>', 0)]")

    def action_generate_order_status_report(self):
        """Generate sale order status report."""
        if self.from_date and self.to_date:
            from_date = str(self.from_date) + ' ' + str(
                datetime.timedelta(hours=0, minutes=0, seconds=0))
            to_date = str(self.to_date) + ' ' + str(
                datetime.timedelta(hours=23, minutes=59, seconds=59))
            domain = [
                ('display_type', '=', False),
                ('product_id.detailed_type', 'in', ['consu', 'product']),
                ('so_date', '>=', from_date),
                ('so_date', '<=', to_date)]
            if self.product_ids:
                domain.append(('product_id', 'in', self.product_ids.ids))
            report_name = "Sale Order Status Report"
            return {
                'name': _(report_name),
                'view_mode': 'tree,form',
                'res_model': 'sale.order.line',
                'domain': domain,
                'type': 'ir.actions.act_window',
                'context': {},
                'target': 'current',
            }

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
            if self.supplier_ids:
                domain.append(
                    ('order_id.partner_id', 'in', self.supplier_ids.ids))

            # report_name = "Purchase Order Status Report"
            action = self.env.ref(
                'bista_orders_report.'
                'action_purchase_order_line_status').sudo().read()[0]
            action.update({'domain': domain})
            return action
