# -*- coding: utf-8 -*-
{
    "name": "Chatter Position",
    "summary": "Chatter Position",
    "version": "15.0.1.0.3",
    'author': "Odoo Being, Odoo Community Association (OCA)",
    'website': "https://www.odoobeing.com",
    'license': "LGPL-3",
    "category": "Extra Tools",
    'images': ['static/description/images/ob_chatter_position.png'],
    'support': 'odoobeing@gmail.com',
    "depends": ["web", "mail"],
    "data": [
        "views/res_users.xml",
        "views/web.xml",
        # "views/assets.xml",
    ],
    'qweb': [
        'static/src/xml/form_buttons.xml',
    ],
    'assets': {
            'web.assets_backend': [
                'ob_chatter_position/static/src/scss/chatter_position.scss',
                'ob_chatter_position/static/src/scss/attachment_viewer.scss',
                'ob_chatter_position/static/src/js/form_chatter_position.js'
            ],
        },
    'installable': True,
    'auto_install': False,
}
