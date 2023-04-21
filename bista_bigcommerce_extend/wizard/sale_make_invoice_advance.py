# -*- coding: utf-8 -*-

from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    # Set False value on fiscal position if it's Down payment invoice
    def _create_invoice(self, order, so_line, amount):
        invoice = super()._create_invoice(order, so_line, amount)
        invoice.write({"fiscal_position_id": False})
        return invoice
