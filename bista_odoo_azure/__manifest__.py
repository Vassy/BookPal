# -*- coding: utf-8 -*-
{
    "name": "Azure Integration",
    "author": "Bista Solutions",
    "website": "https://www.bistasolutions.com",
    "support": "support@bistasolutions.com",
    "category": "Purchase",
    "summary": "",
    "description":
        """ 
        """,
    "version": "15.0.0",
    "depends": ['base', 'documents', 'contacts'],
    "data": [
        'security/ir.model.access.csv',
        'data/create_invoices_from_doc.xml',
        'data/folder_records.xml',
        'data/share_link_record.xml',
        'security/odoo_azure_security.xml',
        'views/azure_model_view.xml',
        'views/res_config_settings_view.xml',
        'views/share_view.xml',
        'views/res_partner_view.xml',
        'views/azure_log_view.xml',
    ],
    "auto_install": False,
    "application": True,
    "installable": True,
}
