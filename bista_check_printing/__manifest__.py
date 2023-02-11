# -*- coding: utf-8 -*-

{
    "name": "US Check Printing",
    "version": "15.0.1.0.0",
    "summary": "Print US Checks",
    "description": """
        This module allows to print your payments on pre-printed check paper.
     """,
    "author": "Bista Solutions",
    "company": "Bista Solutions",
    "category": "Accounting",
    "depends": ["l10n_us_check_printing"],
    "license": "AGPL-3",
    "data": ["views/print_check_views.xml"],
    "installable": True,
    "assets": {
        "web.report_assets_common": ["bista_check_printing/static/**/*"],
    },
}
