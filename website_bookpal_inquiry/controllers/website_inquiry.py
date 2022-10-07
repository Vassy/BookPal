# -*- coding: utf-8 -*-
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request


class WebsiteSale(http.Controller):
    @http.route([
        '''/inquiry''',
    ], type='http', auth="public", website=True)
    def inquiry(self, **post):
        values = {}
        values.update({
            'error': {},
            'error_message': [],
            'products': request.env['product.template'].search([], limit=5)
        })
        return request.render("website_bookpal_inquiry.website_inquiry", values)
