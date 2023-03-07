from odoo import fields, models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    manual_shipping_cost = fields.Float(
        'Manual Shipping Cost')

    def button_confirm(self):
        """Updated manual shippig cost on sale order."""
        if self.delivery_type == 'manual':
            self.order_id.set_delivery_line(
                self.carrier_id, self.manual_shipping_cost)
            self.order_id.write({
                'recompute_delivery_price': False,
                'delivery_message': self.delivery_message,
            })
        else:
            return super(ChooseDeliveryCarrier, self).button_confirm()

    def _get_shipment_rate(self):
        if self.delivery_type == 'manual' and self.carrier_id and self.order_id:
            shipping_line = self.env['sale.order.line'].search(
                [('product_id', '=', self.carrier_id.product_id.id),
                 ('order_id', '=', self.order_id.id)], limit=1)
            self.manual_shipping_cost = shipping_line.price_unit
            return {}
        else:
            return super(ChooseDeliveryCarrier, self)._get_shipment_rate()
