# -*- coding: utf-8 -*-

{
    "name": "Purchase order with Pricelist",
    "summary": """Purchase order with Pricelist""",
    "description": """Purchase order with Pricelist""",
    "license": "LGPL-3",
    "author": "Bista Solutions Pvt Ltd.",
    "website": "http://www.bistasolutions.com",
    "version": "15.0.1.0.2",
    "category": "Purchase Management",
    "depends": ["purchase_stock", "bista_sale_multi_ship"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_pricelist_view.xml",
        "views/purchase_order_view.xml",
        "views/sale_order_views.xml",
        "views/product_supplierinfo_view.xml",
        "views/res_partner_view.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": True,
}
