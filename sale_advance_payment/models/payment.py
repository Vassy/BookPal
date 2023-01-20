# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPayment(models.Model):

    _inherit = "account.payment"

    sale_id = fields.Many2one(
        "sale.order", "Sale", readonly=True, states={"draft": [("readonly", False)]}
    )


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _create_payment(self, **extra_create_values):
        payment = super()._create_payment(**extra_create_values)
        if self.sale_order_ids:
            payment.write({"sale_id": self.sale_order_ids.ids[0]})
        return payment
