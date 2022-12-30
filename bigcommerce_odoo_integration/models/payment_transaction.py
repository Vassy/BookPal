import logging
import re

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.tools import float_compare


_logger = logging.getLogger(__name__)
from odoo.addons.sale.models.payment_transaction import PaymentTransaction


def _check_amount_and_confirm_order(self):
    self.ensure_one()
    for order in self.sale_order_ids.filtered(lambda so: so.state in ('draft', 'sent')):
        _logger.info("Check Amount and Confirm Order:{0} {1}".format(self.amount,order.amount_total))
        if float_compare(self.amount, order.amount_total, 2) == 0:
            # if order.bigcommerce_store_id and order.bigcommerce_store_id.bigcommerce_store_type == 'b2c' and order_id.state != 'sale':
            #     #order.with_context(send_email=True).action_confirm()
            #     order.action_confirm()
            # else:
            #     order.with_context(send_email=True).action_confirm()
            print("Stop Confirming Order While Import Order From BC")
        else:
            _logger.warning(
                '<%s> transaction AMOUNT MISMATCH for order %s (ID %s): expected %r, got %r',
                self.acquirer_id.provider, order.name, order.id,
                order.amount_total, self.amount,
            )
            order.message_post(
                subject=_("Amount Mismatch (%s)", self.acquirer_id.provider),
                body=_(
                    "The order was not confirmed despite response from the acquirer (%s): order total is %r but acquirer replied with %r.") % (
                         self.acquirer_id.provider,
                         order.amount_total,
                         self.amount,
                     )
            )
PaymentTransaction._check_amount_and_confirm_order = _check_amount_and_confirm_order
