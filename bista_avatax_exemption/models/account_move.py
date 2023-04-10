from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_avatax_invoice_lines(self):
        """Skip the down payment line to compute tax."""
        return [
            self._get_avatax_invoice_line(
                product=line.product_id,
                price_subtotal=line.price_subtotal if
                self.move_type == 'out_invoice' else -line.price_subtotal,
                quantity=line.quantity,
                line_id='%s,%s' % (line._name, line.id),
            )
            for line in self.invoice_line_ids.filtered(
                lambda l: not l.display_type and
                (l.product_id and not
                 l.product_id.name.startswith('Down Payment')) or
                not l.product_id)
        ]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_avatax_invoice_lines(self):
        """Skip the down payment line to compute tax."""
        return [
            self._get_avatax_invoice_line(
                product=line.product_id,
                price_subtotal=line.price_subtotal,
                quantity=line.product_uom_qty,
                line_id='%s,%s' % (line._name, line.id),
            )
            for line in self.order_line.filtered(
                lambda l: not l.display_type and
                (
                    l.product_id and
                    not l.product_id.name.startswith('Down Payment')) or
                not l.product_id)
        ]
