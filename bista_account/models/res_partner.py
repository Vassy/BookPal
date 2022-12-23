# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    property_customer_payment_method_id = fields.Many2one(
        "account.payment.method",
        company_dependent=True,
        domain="[('payment_type', '=', 'inbound')]",
    )
