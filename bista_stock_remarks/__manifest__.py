{
    'name': 'Bista Stock Remarks',
    'version': '15.0.1.0.0',
    'description': 'Manage Sale order and Purchase Order custom field "Remark" to stock',
    'category': '',
    'summary': '',
    'website': 'http://www.bistasolutions.com',
    'license': 'AGPL-3',
    'depends': [
           'sale', 'purchase', 'stock', 'bista_report_header_footer',
    ],
    'data': [
        'views/sale_order.xml',
        'views/purchase_order.xml',
        'views/stock_picking.xml',

        # 'report/report_stockpicking_operations.xml',
    ],
    'installable': True,
    'auto_install': False
}
