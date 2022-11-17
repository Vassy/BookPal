# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

{
    "name": "Customer Credit Limit",
    "version": "15.0.0.1",
    "category": "Partner",
    # Dependent module required for this module to be installed
    "depends": ["delivery", "bista_sales_approval"],
    "author": "Bista Solutions Pvt. Ltd.",
    "maintainer": "Bista Solutions Pvt. Ltd.",
    "summary": "Set credit limit for customer.",
    "description": """Customer Credit Limit
        1: Set the credit limit for customers.
        2: if CL < 0, SO move to Credit Review state.
        3: Only 'Can override credit limit' group of users confirm those SO.
    """,
    "website": "https://www.bistasolutions.com",
    "data": [
        "security/ir.model.access.csv",
        "security/partner_credit_limit_security.xml",
        "views/partner_view.xml",
        "views/account_invoice_view.xml",
        "views/sale_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
