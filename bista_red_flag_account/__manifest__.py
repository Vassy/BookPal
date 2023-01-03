# -*- coding: utf-8 -*-
{
    'name': "Bista Red Flag account",
    'summary': """
        This module is used to extend Red Flag functionality
        """,
    'description': """
               This module is used to extend Red Flag functionality
    """,
    'author': "Bista Solutions Pvt. Ltd",
    'license': 'AGPL-3',
    'website': "https://www.bistasolutions.com/",
    'category': 'Sale',
    'version': '0.1',
    'depends': ['base', 'contacts', 'bista_contact'],
    'assets': {
        'web.assets_backend': [
            '/bista_red_flag_account/static/css/partner_clr.css',
            '/bista_red_flag_account/static/js/fieldMany2one_update.js',
        ],
    },
}
