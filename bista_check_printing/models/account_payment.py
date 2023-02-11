# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.misc import formatLang, format_date


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _check_fill_line(self, amount_str):
        return amount_str or ""

    def _check_build_page_info(self, i, p):
        result = super()._check_build_page_info(i, p)
        result["date"] = self.date.strftime("%b %d, %Y")
        return result
