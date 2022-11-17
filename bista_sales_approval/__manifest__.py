# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2022 (https://www.bistasolutions.com)
#
##############################################################################

{
    "name": "Network Craze: SO approval",
    "version": "15.0.1.0.0",
    "author": "Bista Solutions Pvt. Ltd.",
    "category": "Sales",
    "summary": "",
    "description": """Sales approval flow.""",
    "depends": ["sale_management"],
    "website": "https://www.bistasolutions.com",
    "data": [
        "security/sale_security.xml",
        "security/ir.model.access.csv",
        "views/sale_order_approval_button_view.xml",
        "views/product.xml",
        "wizard/so_reject_reason_view.xml",
        "wizard/min_price_wiz.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
