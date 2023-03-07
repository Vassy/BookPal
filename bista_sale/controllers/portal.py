# -*- encoding: utf-8 -*-

from odoo import http
from odoo.http import request

from odoo.addons.sale.controllers.portal import CustomerPortal


class ModCustomerPortal(CustomerPortal):
    @http.route()
    def portal_order_page(
        self,
        order_id,
        report_type=None,
        access_token=None,
        message=False,
        download=False,
        **kw
    ):
        response = super().portal_order_page(
            order_id=order_id,
            report_type=report_type,
            access_token=access_token,
            message=message,
            download=download,
            **kw
        )
        sale_id = request.env["sale.order"].browse(order_id)
        if sale_id.exists() and sale_id.acquirer_ids:
            response.qcontext["acquirers"] = sale_id.acquirer_ids
        return response
