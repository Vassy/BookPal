{
    # App information
    'name': 'Extend BigCommerce Functionality',
    'category': 'integration',
    'author': "Bista Solutions Pvt Ltd.",
    'website': "http://www.bistasolutions.com",
    'version': '15.0.1.0.0',
    'summary': """""",
    'description': """
        Update the bigcommerce functionality.
        """,
    'depends': ['bigcommerce_odoo_integration'],

    'data': [
        'views/product_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': "LGPL-3",
}
