# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    quote_tag_line = fields.Html(related="company_id.quote_tag_line", readonly=False)
    so_tag_line = fields.Html(related="company_id.so_tag_line", readonly=False)


class ResCompany(models.Model):
    _inherit = "res.company"

    quote_tag_line = fields.Html("Quotation Report Tag Line")
    so_tag_line = fields.Html("Sale Order Report Tag Line")
