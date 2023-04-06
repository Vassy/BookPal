# -*- coding: utf-8 -*-

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Overwrite method to change discount (Rounding price unit in vendor bill)
    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        if self.move_id.move_type not in ['in_invoice', 'in_refund'] and not self._context.get('create_bill') and move_type not in ['in_invoice', 'in_refund']:
            return super()._get_price_total_and_subtotal_model(price_unit, quantity, discount, currency, product, partner, taxes, move_type)
        res = {}

        # Compute 'price_subtotal'.
        line_discount_price_unit = currency.round(price_unit * (1 - (discount / 100.0)))
        subtotal = quantity * line_discount_price_unit

        # Compute 'price_total'.
        if taxes:
            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(line_discount_price_unit,
                quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        #In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

    @api.model
    def _get_fields_onchange_balance_model(self, quantity, discount, amount_currency, move_type, currency, taxes, price_subtotal, force_computation=False):
        res = super()._get_fields_onchange_balance_model(quantity, discount, amount_currency, move_type, currency, taxes, price_subtotal, force_computation)
        if self.move_id.move_type in ['in_invoice', 'in_refund'] or self._context.get('create_bill') or move_type in ['in_invoice', 'in_refund']:
            if res.get('price_unit'):
                del res['price_unit']
        return res
