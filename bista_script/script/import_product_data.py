"""Updated the product data."""
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
password = 'a'  # the password of the user
dbname = 'book_pal_new'  # the database
url = 'http://127.0.0.1:8069'  # ESP-staging url

sock_common = xmlrpclib.ServerProxy(url + '/xmlrpc/common')
uid = sock_common.login(dbname, username, password)
sock = xmlrpclib.ServerProxy(url + '/xmlrpc/object')

print ("\n current_path >>>>", current_path)
output = open(current_path + '/Errors.txt', 'w')
file_upload = '/sheet/ProductDataforOdooFinal.xlsx'
# file_upload = 'bista_script/creatio_contacts.xlsx'
book = xlrd.open_workbook(current_path + file_upload)
sheet = book.sheet_by_index(0)

error = False

print("=======START SCRIPT =========")
# sheet.nrows
try:
    for row_no in range(1, 10):  #
        error = False
        row_values = sheet.row_values(row_no)
        prod_tmpl_id = sock.execute(
            dbname, uid, password,
            'product.template',
            'search',
            [('default_code', '=', row_values[0])])
        print ("\n prod_tmpl_id>>>>>.", prod_tmpl_id)

except Exception as e:
    row_values.append(str(e))
    output.write(str(row_values) + '\n')

print("=======SCRIPT COMPLETE =========")
