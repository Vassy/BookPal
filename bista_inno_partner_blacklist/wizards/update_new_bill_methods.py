# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero


class PaymentMethodImprovement(models.TransientModel):
    _name  = 'payment.method.improve'
    _description = 'Payment Method Improvement'

    payment_method_id = fields.Many2one('account.payment.method' , String = "Account Payment Method", required=True)

    def do_update_method(self):
        print("cccccccccccccccccccccc", self.env.context)
        bill_ids = self.env['account.move'].browse(self._context.get('bill_ids'))
        for bill in bill_ids.filtered(lambda x : x.payment_state not in ['paid','in_payment']):
            bill.update({'preferred_payment_method_id' : self.payment_method_id.id})