# -*- coding: utf-8 -*-
{
    'name': "Bista Purchase",
    'summary': """Purchase Customisation""",
    'description': """Purchase Customisation""",
    'license': "LGPL-3",
    'author': "Bista Solutions Pvt Ltd.",
    'website': "http://www.bistasolutions.com",
    'category': "Purchase",
    'version': '15.0.1.0.1',
    'depends': ['purchase_pricelist', 'delivery', 'bista_contact', 'bista_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/email_schdule_activity.xml',
        'data/email_template.xml',
        'data/po_status_line_data.xml',
        'data/ir_sequence_data.xml',
        'data/email_schdule_activity.xml',
        'views/res_partner_views.xml',
        'views/purchase_views.xml',
        'views/stock_picking_views.xml',
        # 'report/purchase.xml',
        # 'report/purchase_quotation_templates.xml',
        # 'report/report_templates.xml',
        'report/purchase_order.xml',
        'report/purchase_quotation.xml',

        # 'report/purchase_order.xml',
        'report/stock_picking.xml',
        'report/account_move.xml',
        # 'wizard/update_shipping_views.xml',
        'wizard/update_shipment_tracking_views.xml',
        'views/purchase_tracking_views.xml',
        # 'report/purchase_order.xml',
        'report/stock_picking.xml',
        

    ],
    'auto_install': False,
    'installable': True,
    'application': True
}
