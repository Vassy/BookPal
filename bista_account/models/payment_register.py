# -*- coding: utf-8 -*-

from odoo import models, api


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.depends("payment_type", "journal_id", "partner_id")
    def _compute_payment_method_line_id(self):
        super()._compute_payment_method_line_id()
        for record in self:
            method_line = record.journal_id.inbound_payment_method_line_ids.filtered(
                lambda l: l.payment_method_id
                == record.partner_id.with_company(
                    record.company_id
                ).property_customer_payment_method_id
            )
            if record.payment_type == "inbound" and method_line:
                record.payment_method_line_id = method_line[0]
