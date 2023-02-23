# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    use_po_terms = fields.Boolean(
        string="Purchase Terms & Conditions",
        config_parameter="bista_purchase.use_po_terms",
    )
    po_terms = fields.Html(related="company_id.po_terms", readonly=False)


class ResCompany(models.Model):
    _inherit = "res.company"

    po_terms = fields.Html()
