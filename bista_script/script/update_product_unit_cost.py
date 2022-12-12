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
password = 'admin'  # the password of the user
dbname = 'nikita-bistait-bookpal-bookpalstaging-5352248'  # the database
# ESP-staging url
url = 'https://nikita-bistait-bookpal-bookpalstaging-5352248.dev.odoo.com'

# dbname = 'book_pal_new'  # the database
# url = 'http://localhost:8069'  # ESP-staging url

sock_common = xmlrpclib.ServerProxy(url + '/xmlrpc/common')
uid = sock_common.login(dbname, username, password)
sock = xmlrpclib.ServerProxy(url + '/xmlrpc/object')

output = open(current_path + '/Errors.txt', 'w')
file_upload = '/sheet/BP_Inventory_12-7-2022.xlsx'
book = xlrd.open_workbook(current_path + file_upload)
sheet = book.sheet_by_index(0)

error = False

print("=======START SCRIPT =========")
# sheet.nrows
try:
    for row_no in range(1, sheet.nrows):  #
        error = False
        row_values = sheet.row_values(row_no)
        prod_vals = {}
        # prod_vals = {
        #     'isbn': row_values[1],
        #     'product_format': row_values[7],
        #     'origin': row_values[8],
        #     'weight': row_values[11],
        # }
        print ("\n row vales >>>>>>>", row_values[1], str(row_values[1]))
        # SKU coming as float value so it is showign with decimal
        # Split that decimal from SKU
        sku = str(row_values[1]).split('.')[0]
        prod_id = sock.execute(
            dbname, uid, password,
            'product.product',
            'search',
            [('default_code', '=', sku)])
        if prod_id and prod_id[0]:
            prod_id = prod_id[0]
            sock.execute(
                dbname, uid, password,
                'product.product',
                'write',
                prod_id,
                {'standard_price': row_values[4]})
            print ("\n prod_id >>>>>standard_price>", prod_id, row_values[4])
            # prod_tmpl_id = sock.execute(
            #     dbname, uid, password,
            #     'product.product', 'read',
            #     prod_id, ['product_tmpl_id'])
            # prod_tmpl_id = prod_tmpl_id and prod_tmpl_id[0] or 0
            # if prod_tmpl_id:
            #     prod_tmpl_id = prod_tmpl_id.get('product_tmpl_id')[0]
            # print("\n prod_tmpl_id >>final>>>", prod_tmpl_id)

except Exception as e:
    row_values.append(str(e))
    output.write(str(row_values) + '\n')
    output.write('Product SKU : ' +
                 str(row_values[0]) + '\n')

print("=======SCRIPT COMPLETE =========")
