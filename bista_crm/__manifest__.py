# -*- coding: utf-8 -*-
{
    "name": "Bista CRM",
    "version": "15.0.1.1.0",
    "description": "Manage CRM",
    "category": "CRM",
    "summary": "Manage CRM",
    "website": "http://www.bistasolutions.com",
    "license": "AGPL-3",
    "depends": ["sale_crm", "bigcommerce_odoo_integration", "bista_sales_approval"],
    "data": [
        "security/ir.model.access.csv",
        "data/shipping_price_type_data.xml",
        "data/fullfillment_warehouse_data.xml",
        "data/deal_source_data.xml",
        "views/configuration_view.xml",
        "views/crm_lead_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
