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
# username = 'admin'  # the user
# password = 'admin'
# password = 'BookPal@2022'  # the password of the user
# dbname = 'nikita-bistait-bookpal-bista-staging-5356920'  # the database
# ESP-staging url
# url = 'https://nikita-bistait-bookpal-bista-staging-5356920.dev.odoo.com'

# UAT url

# dbname = 'nikita-bistait-bookpal-bookpalstaging-5352248'
# url = 'https://nikita-bistait-bookpal-bookpalstaging-5352248.dev.odoo.com'

# local Url
# dbname = 'BookPalStaging-Dec-14'  # the database
# url = 'http://localhost:8069'  # ESP-staging url

# dbname = 'Bista-staging-jan-23-sandbox'  # the database
# url = 'http://0.0.0.0:8070'  # ESP-staging url

# production url
url = 'https://bookpal.odoo.com'
dbname = 'nikita-bistait-bookpal-production-5352226'
username = "admin"
password = "admin"

sock_common = xmlrpclib.ServerProxy(url + '/xmlrpc/common')
uid = sock_common.login(dbname, username, password)
sock = xmlrpclib.ServerProxy(url + '/xmlrpc/object')

output = open(current_path + '/Errors.txt', 'w')
# file_upload1 = '/sheet/ProductVendorPricelist.xlsx'
file_upload = '/sheet/BP_Inventory_master.xlsx'
book = xlrd.open_workbook(current_path + file_upload)
sheet = book.sheet_by_index(0)


error = False

print("=======START SCRIPT =========")

try:
    for row_no in range(1, sheet.nrows):  #
        error = False
        row_values = sheet.row_values(row_no)
        print ("\n row values >>>", row_no, row_values)
        prod_vals = {
            'standard_price': row_values[4],
        }
        prod = row_values[1]
        if isinstance(row_values[1], float):
            prod = str(int(row_values[1]))
        # print ("\n prod >>>>>>", prod)
        prod_id = sock.execute(
            dbname, uid, password,
            'product.template',
            'search',
            [('default_code', '=', prod)])
        prod_id = prod_id and prod_id[0] or False
        print ("\n prod_id >>>", prod_id)
        sock.execute(
            dbname, uid, password,
            'product.template',
            'write',
            prod_id,
            prod_vals)
except Exception as e:
    row_values.append(str(e))
    output.write(str(row_values) + '\n')
    output.write('Product ref : ' +
                 str(row_values))

print("=======SCRIPT COMPLETE =========")
