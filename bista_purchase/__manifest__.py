# -*- coding: utf-8 -*-
{
    'name': "Bista Purchase",
    'summary': """Purchase Customisation""",
    'description': """Purchase Customisation""",
    'license': "LGPL-3",
    'author': "Bista Solutions Pvt Ltd.",
    'website': "http://www.bistasolutions.com",
    'category': "Purchase",
    'version': '15.0.1.2.1',
    'depends': ['purchase_pricelist', 'bista_contact', 'bista_sale', 'bista_stock_remarks', 'bista_orders_report', 'web_tree_many2one_clickable'],
    'data': [
        'security/ir.model.access.csv',

        'report/purchase_backorder_view.xml',
        'report/purchase_order.xml',
        'report/purchase_quotation.xml',
        'report/account_move.xml',
        'report/stock_picking.xml',
        "report/purchase_report.xml",

        'data/email_schdule_activity.xml',
        'data/email_template.xml',
        'data/po_status_line_data.xml',
        'data/ir_sequence_data.xml',
        'data/email_schdule_activity.xml',
        'data/master_data_all_file.xml',
        'data/purchase_approval_data.xml',

        'views/po_status_line_log_views.xml',
        'views/purchase_views.xml',
        'wizard/update_shipment_tracking_views.xml',
        'wizard/order_reject_view.xml',
        'views/res_partner_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
        'views/res_partner_views.xml',
        'views/purchase_views.xml',
        'views/stock_picking_views.xml',
        'views/purchase_tracking_views.xml',
        "views/product_views.xml",
        "views/res_config_settings_views.xml",
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_qweb': [
            'bista_purchase/static/src/xml/**/*',
        ],
    },
}
# for Odoo.sh update