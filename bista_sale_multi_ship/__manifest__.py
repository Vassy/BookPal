# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Sale Multi Ship',
    'description': """
        Sales Multi Ship
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'version': '15.0.0.1',

    # Dependent module required for this module to be installed
    'depends': ['sale',
                'delivery_ups', 'contacts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/product_data.xml',
        'wizard/put_in_pack_wizard_view.xml',
        'wizard/external_shipping_wizard_view.xml',
        'views/res_partner_view.xml',
        'views/sale_multi_ship.xml',
        'views/sale_order_view.xml',
        'views/stock_view.xml',
        'report/shipment_report_view.xml',
        'report/report_register.xml',
        # 'data/email_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
