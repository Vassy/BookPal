{
    'name': 'Bista Sale',
    'version': '15.0.1.4.2',
    'description': 'Manage Sale order',
    'category': 'Sale',
    'summary': 'Manage Sale',
    'website': 'http://www.bistasolutions.com',
    'license': 'AGPL-3',
    'depends': ['contacts',
                'bista_sale_multi_ship',
                'bista_bigcommerce_extend',
                'stock_dropshipping',
                # added dpendancy for compute picking based on dropshipping
                'account_followup',
                # used total_due field of this module as related field in SO
                ],
    'assets': {
        'web.assets_backend': [
            'bista_sale/static/src/css/custome_field.css',
        ]
    },
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'report/sale.xml',
        # 'report/sale_delivery_report.xml',
        'views/artwork_status_view.xml',
        'views/sale_order_view.xml',
        'views/stock_picking_view.xml',
        'views/white_glove_type_view.xml',
        'views/journal_customization_view.xml',
        'views/death_type_view.xml',
        'views/customization_type_view.xml',
        # 'views/product_view.xml',
        "views/sale_templates.xml",
        "views/product_views.xml",
        "views/seller_report_views.xml",
        # "views/crm_lead_views.xml",
        "wizard/best_seller_report_views.xml",

    ],
    'installable': True,
    'auto_install': False
}
