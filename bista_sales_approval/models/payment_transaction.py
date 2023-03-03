# -*- encoding: utf-8 -*-

from odoo import models


class Transaction(models.Model):
    _inherit = "payment.transaction"

    def _set_pending(self, state_message=None):
        super()._set_pending(state_message)
        self.sale_order_ids.action_order_booked()

    def _set_authorized(self, state_message=None):
        super()._set_authorized(state_message)
        self.sale_order_ids.action_order_booked()

    def _set_done(self, state_message=None):
        super()._set_done(state_message)
        self.sale_order_ids.action_order_booked()
