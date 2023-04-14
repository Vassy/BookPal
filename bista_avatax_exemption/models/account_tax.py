
from odoo import models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    def compute_all(
            self, price_unit, currency=None, quantity=1.0,
            product=None, partner=None, is_refund=False,
            handle_price_include=True, include_caba_tags=False):
        """Rounded the price unit."""
        price_unit = round(price_unit, 2)
        return super(AccountTax, self).compute_all(
            price_unit, currency, quantity,
            product, partner, is_refund, handle_price_include,
            include_caba_tags)
