# -*- coding: utf-8 -*-
{
    'name': 'Bista CRM',
    'version': '15.0.1.0.0',
    'description': 'Manage CRM',
    'category': 'CRM',
    'summary': 'Manage CRM',
    'website': 'http://www.bistasolutions.com',
    'license': 'AGPL-3',
    'depends': ['sale_crm'],
    'data': [
        # Views
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'auto_install': False
}
