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
    'depends': ['purchase', 'delivery'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True
}
