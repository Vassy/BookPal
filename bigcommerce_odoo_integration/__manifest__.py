{
    # App information
    'name': 'BigCommerce Odoo Integration',
    'category': 'Website',
    'author': "Vraja Technologies",
    'version': '15.0.1.1.1',
    'summary': """""",
    'description': """
    BigCommerce Odoo Integration will help you connect with Bigcommerce and Easily Perform Import and Export Operation. 
    Import Order,Product Customer,Product Category,Multiple Images From Bigcommerce to odoo.
    Export Order,Shipment,Product,Inventory From Odoo to Bigcommerce.
    We also Provide the fedex,usps,easyship,stamp.com,ebay
""",

    'depends': ['delivery', 'sale_management', 'product',
                'sale_stock', 'sale_advance_payment'],

    'data': [
        'data/delivery_demo.xml',
        'data/ir_cron.xml',
        'data/payment_acquire.xml',
        'security/ir.model.access.csv',
        'wizard/export_and_update_product_to_bc.xml',
        'wizard/bigcommerce_import_operation.xml',
        'wizard/bigcommerce_export_operation.xml',
        'views/warehouse.xml',
        'views/res_company.xml',
        'views/bc_store_listing.xml',
        'views/bc_store_listing_items.xml',
        'views/bigcommerce_store_configuration_view.xml',
        'views/bigcommerce_operation_details.xml',
        'views/product_category.xml',
        'views/product_template.xml',
        'views/product_attribute.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        # "views/bigcommerce_product_image_view.xml",
        'views/bigcommerce_stock_picking_view.xml',
        'views/bc_product_brand.xml',
        'views/menuitem.xml',
    ],

    'images': ['static/description/bigcommerce_cover_image.png'],
    'maintainer': 'Vraja Technologies',
    'website': 'https://www.vrajatechnologies.com',
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': '450',
    'currency': 'EUR',
    'license': 'OPL-1',

}
# version changelog
# 14.0.24.08.2021 (Improve UI)
# 14.0.25.08.2021 (set parent_id in categories)
# 14.0.14.10.2021 (added more features and improve listing functionality)
# removed website dependency
