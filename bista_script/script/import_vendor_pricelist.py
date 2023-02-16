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
password = 'admin'
# password = 'BookPal@2022'  # the password of the user
# dbname = 'nikita-bistait-bookpal-bista-staging-5356920'  # the database
# ESP-staging url
# url = 'https://nikita-bistait-bookpal-bista-staging-5356920.dev.odoo.com'

# UAT url

# dbname = 'nikita-bistait-bookpal-bookpalstaging-5352248'
# url = 'https://nikita-bistait-bookpal-bookpalstaging-5352248.dev.odoo.com'

dbname = 'BookPalStaging-Dec-14'  # the database
url = 'http://localhost:8069'  # ESP-staging url

# dbname = 'Bista-staging-jan-23-sandbox'  # the database
# url = 'http://0.0.0.0:8070'  # ESP-staging url

sock_common = xmlrpclib.ServerProxy(url + '/xmlrpc/common')
uid = sock_common.login(dbname, username, password)
sock = xmlrpclib.ServerProxy(url + '/xmlrpc/object')

output = open(current_path + '/Errors.txt', 'w')
# file_upload1 = '/sheet/ProductVendorPricelist.xlsx'
file_upload = '/sheet/ProductVendorPricelistUpdated.xlsx'
book = xlrd.open_workbook(current_path + file_upload)
sheet = book.sheet_by_index(0)


error = False

print("=======START SCRIPT =========")
products = sock.execute(
    dbname, uid, password,
    'res.partner',
    'search',
    [('name', '=', 'Ricky Manthey')])
for prod in products:
    print("\n product>>>>>>", prod)
    sock.execute(
        dbname, uid, password,
        'res.partner',
        'write',
        prod,
        {'parent_id': False})
# sheet.nrows
# try:
#     for row_no in range(1, sheet.nrows):  #
#         error = False
#         row_values = sheet.row_values(row_no)
#         print ("\n row values >>>", row_no, row_values)
#         prod_vals = {}
#         if not row_values[3]:
#             continue
#         # prod_vals = {
#         #     'isbn': row_values[1],
#         #     'product_format': row_values[7],
#         #     'origin': row_values[8],
#         #     'weight': row_values[11],
#         # }
#         prod = row_values[1]
#         if isinstance(row_values[1], float):
#             prod = str(int(row_values[1]))
#         # print ("\n prod >>>>>>", prod)
#         prod_id = sock.execute(
#             dbname, uid, password,
#             'product.template',
#             'search',
#             [('default_code', '=', prod)])
#         prod_id = prod_id and prod_id[0] or False
#         # print ("\n prod_id >>>", prod_id)
#         if not prod_id:
#             output.write(str(row_values) + '\n')
#             output.write('\n Product not available ;' +
#                          str(row_values[1]) + ';' +
#                          str(row_values[2]) + ';' +
#                          str(row_values[3]) + ';')
#             continue
#         vendor_id = sock.execute(
#             dbname, uid, password,
#             'res.partner',
#             'search',
#             [('name', '=', row_values[2]),
#              ('supplier_rank', '>', 0)])
#         vendor_id = vendor_id and vendor_id[0] or False
#         # print ("\n vendor name >>>", row_values[2], vendor_id)
#         pricelist_name = row_values[3]
#         if isinstance(row_values[3], float):
#             pricelist_name = str(int(row_values[3] * 100)) + '%'
#         print ("\n pricelist_name >>>.", pricelist_name, row_values[3])
#         pricelist_id = sock.execute(
#             dbname, uid, password,
#             'product.pricelist',
#             'search',
#             [('name', '=', pricelist_name),
#              ('used_for', '=', 'purchase')])
#         pricelist_id = pricelist_id and pricelist_id[0]
#         # print ("\n pricelist_id .>>>>>.", pricelist_id)
#         percentage = pricelist_name
#         discount = ''
#         for per in percentage:
#             if per.isdigit():
#                 discount += per
#         # print ("\n percentage >>>>", discount)
#         if not discount.isdigit():
#             output.write(str(row_values) + '\n')
#             output.write('\n Percentage not available ;' +
#                          str(row_values[1]) + ';' +
#                          str(row_values[2]) + ';' +
#                          str(row_values[3]) + ';')
#             continue
#         if not pricelist_id:
#             pricelist_vals = {
#                 'name': pricelist_name,
#                 'used_for': 'purchase',
#                 'item_ids': [(0, 0, {
#                     'compute_price': 'percentage',
#                     'percent_price': float(discount),
#                     'applied_on': '1_product',
#                     'product_tmpl_id': prod_id
#                 })]
#             }
#             pricelist_id = sock.execute(
#                 dbname, uid, password,
#                 'product.pricelist',
#                 'create',
#                 pricelist_vals)
#         pricelist_rule = sock.execute(
#             dbname, uid, password,
#             'product.pricelist.item',
#             'search',
#             [('pricelist_id', '=', pricelist_id),
#              ('product_tmpl_id', '=', prod_id),
#              ('applied_on', '=', '1_product'),
#              ('compute_price', '=', 'percentage'),
#              ('percent_price', '=', float(discount))])
#         # print ("\n pricelist_rule> >>>>", pricelist_rule)
#         if not pricelist_rule:
#             price_rule_vals = {
#                 'compute_price': 'percentage',
#                 'percent_price': float(discount),
#                 'applied_on': '1_product',
#                 'product_tmpl_id': prod_id,
#                 'pricelist_id': pricelist_id
#             }
#             sock.execute(
#                 dbname, uid, password,
#                 'product.pricelist.item',
#                 'create',
#                 price_rule_vals)
#         print ("\n prod, vendor_id, pricelist >>>", prod_id, vendor_id, pricelist_id)
#         if prod_id and vendor_id and pricelist_id:
#             supplier_info = sock.execute(
#                 dbname, uid, password,
#                 'product.supplierinfo',
#                 'search',
#                 [('name', '=', vendor_id),
#                  ('product_tmpl_id', '=', prod_id),
#                  ('min_qty', '=', 0)])
#             # print ("\n supplier_info >>>>", supplier_info)
#             for vlist in supplier_info:
#                 sock.execute(
#                     dbname, uid, password,
#                     'product.supplierinfo',
#                     'write',
#                     vlist, {'vendor_pricelist_id': pricelist_id})
#             if not supplier_info:
#                 supplier_info_vals = {
#                     'name': vendor_id,
#                     'product_tmpl_id': prod_id,
#                     'min_qty': 0,
#                     'vendor_pricelist_id': pricelist_id
#                 }
#                 supplier_info = sock.execute(
#                     dbname, uid, password,
#                     'product.supplierinfo',
#                     'create',
#                     supplier_info_vals)

# except Exception as e:
#     row_values.append(str(e))
#     output.write(str(row_values) + '\n')
#     output.write('Product ref : ' +
#                  str(row_values))

# print("=======SCRIPT COMPLETE =========")
