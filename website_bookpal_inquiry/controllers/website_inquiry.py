# -*- coding: utf-8 -*-
import json
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request

class Inquiry(http.Controller):
    @http.route([
        '''/inquiry''',
    ], type='http', auth="public", website=True)
    def inquiry(self, **post):
        values = {
            'products': request.env['product.template'].sudo().search([('bigcommerce_product_id', '!=', False)])
        }
        return request.render("website_bookpal_inquiry.website_inquiry", values)

    @http.route([
        '''/inquiry-submit''',
    ], type='http', auth="public", website=True)
    def inquiry_submit(self, **post):
        values = {}
        if post:
            sale_order = self.create_quote_from_inquiry(**post)
            return json.dumps({'sale_order_id': sale_order.id, 'sale_order_name': sale_order.name})
        return request.render("website_bookpal_inquiry.website_inquiry", values)

    def create_quote_from_inquiry(self, **post):
        email = post.get('email')
        partner_id = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
        if not partner_id:
            partner_id = partner_id.create({
                'name': email,
                'email': email,
            })
        order_lines = []
        sale_order_id = request.env['sale.order'].sudo().create({
            'partner_id': partner_id.id,
            'note': post.get('notes'),
            # 'order_line': order_lines,
        })
        if post.get('product_id'):
            request.env['sale.order.line'].sudo().create({
                'order_id': sale_order_id.id,
                'product_id': int(post.get('product_id')),
                'product_uom_qty': post.get('quantity'),
            })
        return sale_order_id
