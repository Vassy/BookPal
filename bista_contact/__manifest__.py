# -*- coding: utf-8 -*-
{
    'name': 'Bista Contact',
    'version': '15.0.1.2.1',
    'description': 'Manage Conatct',
    'category': 'Contact',
    'summary': 'Manage Conatct',
    'website': 'http://www.bistasolutions.com',
    'license': 'AGPL-3',
    'depends': ['base', 'product'],
    'data': [
        'security/ir.model.access.csv',

        'views/res_partner_views.xml',
        'wizard/contact_status_update_views.xml',


    ],
    'installable': True,
    'auto_install': False
}
