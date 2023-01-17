# -*- coding: utf-8 -*-

{
    'name': 'Bista Inventory',
    'version': '15.0.1.1.0',
    'description': 'Manage Inventory',
    'category': 'Inventory',
    'summary': 'Manage Inventory',
    'website': 'http://www.bistasolutions.com',
    'license': 'AGPL-3',
    'depends': ['stock', 'bista_sale_multi_ship'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'auto_install': False
}
