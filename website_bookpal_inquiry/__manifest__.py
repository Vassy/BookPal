# -*- coding: utf-8 -*-
{
    'name': "Website Bookpal Inquiry",
    'summary': """Website Bookpal Inquiry""",
    'description': """Website Bookpal Inquiry""",
    'license': "LGPL-3",
    'author': "Bista Solutions Pvt Ltd.",
    'website': "http://www.bistasolutions.com",
    'version': "15.0.1.0.1",
    'category': "Website",
    'depends': ["portal"],
    'data': [
        # "data/website_menu.xml",
        "views/templates.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            'website_bookpal_inquiry/static/src/js/website_inquiry.js',
        ]
    },
    'auto_install': False,
    'installable': True,
    'application': True
}
