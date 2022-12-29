# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2022 (https://www.bistasolutions.com)
#
##############################################################################

{
    "name": "Sale Order Approval",
    "version": "15.0.1.1.0",
    "author": "Bista Solutions Pvt. Ltd.",
    "category": "Sales",
    "description": "Sales Order approval flow",
    "depends": ["sale_management"],
    "website": "https://www.bistasolutions.com",
    "data": [
        "security/sale_security.xml",
        "security/ir.model.access.csv",
        "data/sale_approval_data.xml",
        "data/quote_approve_email_template.xml",
        "views/sale_order_approval_button_view.xml",
        "views/sale_portal_template.xml",
        "wizard/so_reject_reason_view.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
