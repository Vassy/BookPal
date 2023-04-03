# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_available_acquirer(self):
        payment = self.env["payment.acquirer"].sudo()
        payment_ids = payment._get_compatible_acquirers(
            company_id=self.env.company.id,
            partner_id=self.env.user.partner_id.id,
        )
        return [("id", "in", payment_ids.ids)]

    acquirer_ids = fields.Many2many(
        "payment.acquirer",
        string="Available Payments",
        domain=lambda self: self._get_available_acquirer(),
    )
