{
    'name': 'Bista Sale',
    'version': '15.0.1.1.0',
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
        # security
        'security/ir.model.access.csv',
        # views
        'views/artwork_status_view.xml',
        'views/sale_order_view.xml',
        'views/stock_picking_view.xml',
        'views/white_glove_type_view.xml',
        'views/journal_customization_view.xml',
        'views/death_type_view.xml',
        'views/customization_type_view.xml',
        # report
        # 'report/sale_delivery_report.xml',
        'report/sale.xml',
        'data/data.xml',
        "views/sale_templates.xml",
    ],
    'installable': True,
    'auto_install': False
}
