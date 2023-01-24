# """Updated the product data."""
from xmlrpc import client as xmlrpclib
import xlrd
import os
import ssl
import sys

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context
os.chdir('../')
current_path = os.getcwd()
sys.path.append(current_path)
username = 'admin'  # the user
password = 'BookPal@2022'  # the password of the user
# dbname = 'nikita-bistait-bookpal-bista-staging-5356920'  # the database
# ESP-staging url
# url = 'https://nikita-bistait-bookpal-bista-staging-5356920.dev.odoo.com'

# UAT url

dbname = 'nikita-bistait-bookpal-bookpalstaging-5352248'
url = 'https://nikita-bistait-bookpal-bookpalstaging-5352248.dev.odoo.com'

# dbname = 'BookPalStaging-Dec-14'  # the database
# url = 'http://localhost:8069'  # ESP-staging url

sock_common = xmlrpclib.ServerProxy(url + '/xmlrpc/common')
uid = sock_common.login(dbname, username, password)
sock = xmlrpclib.ServerProxy(url + '/xmlrpc/object')

print("\n current_path >>>>", current_path)
output = open(current_path + '/Errors.txt', 'w')
file_upload = '/sheet/ProductVendorPricelist.xlsx'
book = xlrd.open_workbook(current_path + file_upload)
sheet = book.sheet_by_index(0)

error = False

print("=======START SCRIPT =========")
products = sock.execute(
    dbname, uid, password,
    'product.product',
    'search',
    [('detailed_type', '!=', 'service'),
     ('avatax_category_id', '=', False)])
for prod in products:
    print("\n product>>>>>>", prod)
    sock.execute(
        dbname, uid, password,
        'product.product',
        'write',
        prod,
        {'avatax_category_id': 428})
# sheet.nrows
# try:
    # for row_no in range(1, 3):  #
    #     error = False
    #     row_values = sheet.row_values(row_no)
    #     prod_vals = {}
    #     if not row_values[2]:
    #         continue
    #     # prod_vals = {
    #     #     'isbn': row_values[1],
    #     #     'product_format': row_values[7],
    #     #     'origin': row_values[8],
    #     #     'weight': row_values[11],
    #     # }
    #     prod_id = sock.execute(
    #         dbname, uid, password,
    #         'product.template',
    #         'search',
    #         [('default_code', '=', row_values[0])])
    #     print("\n product>>>>>.", prod_id, row_values[0])
    #     prod_id = prod_id and prod_id[0] or False
    #     vendor_id = sock.execute(
    #         dbname, uid, password,
    #         'res.partner',
    #         'search',
    #         [('name', '=', row_values[1]),
    #          ('supplier_rank', '>', 0)])
    #     vendor_id = vendor_id and vendor_id[0] or False
    #     pricelist_id = sock.execute(
    #         dbname, uid, password,
    #         'product.pricelist',
    #         'search',
    #         [('name', '=', row_values[2]),
    #          ('used_for', '=', 'purchase')])
    #     pricelist_id = pricelist_id and pricelist_id[0]
    #     if not pricelist_id:

    #         percentage = row_values[2].split('%')[0]
    #         if not percentage.isdigit():
    #             # output.write(str(row_values) + '\n')
    #             output.write('\n Percentage not available ;' +
    #                          str(row_values[0]) + ';' +
    #                          str(row_values[1]) + ';' +
    #                          str(row_values[2]) + ';')
    #             continue
    #         pricelist_vals = {
    #             'name': row_values[2],
    #             'used_for': 'purchase',
    #             'item_ids': [(0, 0, {
    #                 'compute_price': 'percentage',
    #                 'percent_price': float(percentage),
    #                 'applied_on': '1_product',
    #                 'product_tmpl_id': prod_id
    #             })]
    #         }
    #         pricelist_id = sock.execute(
    #             dbname, uid, password,
    #             'product.pricelist',
    #             'create',
    #             pricelist_vals)
    #     if prod_id and vendor_id and pricelist_id:
    #         supplier_info = sock.execute(
    #             dbname, uid, password,
    #             'product.supplierinfo',
    #             'search',
    #             [('name', '=', vendor_id),
    #              ('product_tmpl_id', '=', prod_id),
    #              ('min_qty', '=', 0)])
    #         for vlist in supplier_info:
    #             sock.execute(
    #                 dbname, uid, password,
    #                 'product.supplierinfo',
    #                 'write',
    #                 vlist, {'vendor_pricelist_id': pricelist_id})
    #         if not supplier_info:
    #             supplier_info_vals = {
    #                 'name': vendor_id,
    #                 'product_tmpl_id': prod_id,
    #                 'min_qty': 0,
    #                 'vendor_pricelist_id': pricelist_id
    #             }
    #             supplier_info = sock.execute(
    #                 dbname, uid, password,
    #                 'product.supplierinfo',
    #                 'create',
    #                 supplier_info_vals)

# except Exception as e:
#     row_values.append(str(e))
#     output.write(str(row_values) + '\n')
#     output.write('Product ref : ' +
#                  str(row_values))

# print("=======SCRIPT COMPLETE =========")
