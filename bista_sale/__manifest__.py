{
    'name': 'Bista Sale',
    'version': '15.0.1.5.2',
    'description': 'Manage Sale order',
    'category': 'Sale',
    'summary': 'Manage Sale',
    'website': 'http://www.bistasolutions.com',
    'license': 'AGPL-3',
    'depends': ['bista_sale_multi_ship',
                'sale_margin',  # change margin string
                'stock_dropshipping',
                # added dpendancy for compute picking based on dropshipping
                'account_followup',
                # used total_due field of this module as related field in SO
                ],
    'assets': {
        'web.report_assets_common': [
            'bista_sale/static/src/css/custome_field.css',
        ]
    },
    'data': [
        'data/data.xml',
        'data/email_template_data.xml',
        "report/report_header_footer_views.xml",
        'report/sale.xml',
        'report/so_delivery_report.xml',
        'security/ir.model.access.csv',
        'security/security_view.xml',
        'views/mail_wizard_invite.xml',
        'views/artwork_status_view.xml',
        "views/res_partner_views.xml",
        'views/sale_order_view.xml',
        'views/white_glove_type_view.xml',
        'views/journal_customization_view.xml',
        'views/death_type_view.xml',
        'views/customization_type_view.xml',
        "views/sale_templates.xml",
        "views/product_views.xml",
        "views/share_template.xml",
        "views/seller_report_views.xml",
        "views/res_config_settings_views.xml",
        "wizard/best_seller_report_views.xml",
        "wizard/update_seller_report_views.xml",
    ],
    'installable': True,
    'auto_install': False
}
