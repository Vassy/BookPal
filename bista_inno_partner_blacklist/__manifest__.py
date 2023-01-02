# -*- coding: utf-8 -*-
{
    'name': "Bista Inno Food Extended",
    'summary': """
        This module is used to extend inno functionality
        """,
    'description': """
               This module is used to extend inno functionality
    """,
    'author': "Bista Solutions Pvt. Ltd",
    'license': 'AGPL-3',
    'website': "https://www.bistasolutions.com/",
    'category': 'Sale',
    'version': '0.1',
    'depends': ['base', 'contacts', 'bista_contact'],
    # 'data': [
    #     'security/ir.model.access.csv',
    #     'views/cheque_details.xml',
    #     'views/views.xml',
    #     'views/sale_order_filter.xml',
    #     'views/purchase_order_filter.xml',
    #     'wizards/payment_method_update.xml',
    #     'views/account_move_inherit.xml',
    #     'views/res_partner.xml',
    #     'views/inventory_report_inherit.xml',
    #     'views/mrp_bom_inherit.xml',
    #     'views/inventory_dashboard.xml',
    #     'views/ar_ap_currency_filter.xml',
    #     'views/stock_quant_inherit.xml',
    #     # 'views/payment_method_update.xml'
    #     'views/stock_move_menu_access.xml',
    #     'views/account_payment_inherit.xml',
    #     'views/manufacturing.xml',
    # ],
    'assets': {
        'web.assets_backend': [
            '/bista_inno_partner_blacklist/static/css/partner_clr.css',
            '/bista_inno_partner_blacklist/static/js/fieldMany2one_update.js',
        ],
    },
    'demo': [

    ],
}
