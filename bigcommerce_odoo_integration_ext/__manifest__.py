{
    # App information
    'name': 'BigCommerce Odoo Integration Pricelist',
    'category': 'Website',
    'author': "Vraja Technologies",
    'version': '15.0.1.1.1',
    'summary': """""",
    'description': """
    BigCommerce Odoo Integration will help you connect with Bigcommerce
    and Easily Perform Import and Export Operation.
    Import Order,Product Customer,Product Category,Multiple Images
    From Bigcommerce to odoo.
    Export Order,Shipment,Product,Inventory From Odoo to Bigcommerce.
    We also Provide the fedex,usps,easyship,stamp.com,ebay
""",

    'depends': ['bista_bigcommerce_extend'],

    'data': [
        'views/product_template.xml',
    ],
    'maintainer': 'Vraja Technologies',
    'website': 'https://www.vrajatechnologies.com',
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
}
