# -*- coding: utf-8 -*-
{
    'name': "Bookpal Import",
    'summary': """Bookpal Import""",
    'description': """Bookpal Import""",
    'license': "LGPL-3",
    'author': "Bista Solutions Pvt Ltd.",
    'website': "http://www.bistasolutions.com",
    'category': "Purchase",
    'version': '15.0.1.0.1',
    'depends': ['bista_purchase'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'wizard/import_vendor_views.xml',
        'wizard/import_vendor_pricelist_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True
}
