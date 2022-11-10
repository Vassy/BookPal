
from odoo import fields, models, _
import datetime


class SaleOrderReportWiz(models.TransientModel):
    _name = 'sale.order.status.report.wiz'
    _description = 'Sale Order Report Wizard'

    from_date = fields.Date(
        string="From Date",
        default=datetime.datetime.today().replace(day=1))
    to_date = fields.Date(
        string="To Date", default=fields.Date.context_today)
    product_ids = fields.Many2many('product.product', string="Products")
    amazon_orders = fields.Boolean('Amazon Orders')

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
            if self.amazon_orders:
                domain.append(('order_id.amz_seller_id', '!=', False))
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
