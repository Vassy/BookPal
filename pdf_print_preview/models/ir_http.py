# -*- coding: utf-8 -*-

from odoo import models
from odoo.http import request


class Http(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super(Http, self).session_info()
        print("__________RESULT__________", result)
        user = request.env.user
        print("_________USER____________", user)
        result.update({
            "preview_print": user.preview_print,
            "automatic_printing": user.automatic_printing,
            "report_layout": bool(user.company_id.external_report_layout_id)
        })
        print("_________UPDATED-RESULT__________", result)
        return result
