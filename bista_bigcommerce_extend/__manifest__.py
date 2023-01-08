{
    # App information
    'name': 'Extend BigCommerce Functionality',
    'category': 'integration',
    'author': "Bista Solutions Pvt Ltd.",
    'website': "http://www.bistasolutions.com",
    'version': '15.0.2.2.1',
    'summary': """""",
    'description': """
        Update the bigcommerce functionality.
        """,
    'depends': ['bigcommerce_odoo_integration',
                'account_avatax_sale'],

    'data': [
        'views/product_template.xml',
        'views/res_partner_view_extend.xml',
        'views/bigcommerce_configuration_view.xml',
        'views/bigcommerce_operation_view.xml',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': "LGPL-3",
}
