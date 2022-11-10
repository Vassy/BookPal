# -*- coding: utf-8 -*-
# from odoo import http


# class ./expressSignGit/bistaPendingOrdersReport(http.Controller):
#     @http.route('/./express_sign_git/bista_pending_orders_report/./express_sign_git/bista_pending_orders_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/./express_sign_git/bista_pending_orders_report/./express_sign_git/bista_pending_orders_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('./express_sign_git/bista_pending_orders_report.listing', {
#             'root': '/./express_sign_git/bista_pending_orders_report/./express_sign_git/bista_pending_orders_report',
#             'objects': http.request.env['./express_sign_git/bista_pending_orders_report../express_sign_git/bista_pending_orders_report'].search([]),
#         })

#     @http.route('/./express_sign_git/bista_pending_orders_report/./express_sign_git/bista_pending_orders_report/objects/<model("./express_sign_git/bista_pending_orders_report../express_sign_git/bista_pending_orders_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('./express_sign_git/bista_pending_orders_report.object', {
#             'object': obj
#         })
