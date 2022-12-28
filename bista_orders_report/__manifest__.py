# -*- coding: utf-8 -*-
{
    'name': "Bista Order Reports",
    'summary': """
        This module is used to get the report of all
        delivered and non delivered quantities in
        Sale order
        """,
    'description': """
        This module is used to get the report of all
        delivered and non delivered quantities in
        Sale order(Screen Report)
    """,
    'author': "Bista Solutions Pvt. Ltd",
    'license': 'AGPL-3',
    'website': "https://www.bistasolutions.com/",
    'category': 'Sale',
    'version': '0.1',
    'depends': [
                'sale',
                'sale_stock',
                'purchase_stock',
                'bista_sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/order_status_report_wiz.xml',
        'views/sale_order_line_view.xml',
        'views/purchase_order_line_view.xml',
    ],
    'demo': [],
}
