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
# dbname = 'nikita-bistait-bookpal-bista-staging-5356920'  # the database
# ESP-staging url
# url = 'https://nikita-bistait-bookpal-bista-staging-5356920.dev.odoo.com'

dbname = 'book_pal_new'  # the database
url = 'http://localhost:8069'  # ESP-staging url

sock_common = xmlrpclib.ServerProxy(url + '/xmlrpc/common')
uid = sock_common.login(dbname, username, password)
sock = xmlrpclib.ServerProxy(url + '/xmlrpc/object')

print ("\n current_path >>>>", current_path)
output = open(current_path + '/Errors.txt', 'w')
file_upload = '/sheet/ProductDataforOdooFinal.xlsx'
book = xlrd.open_workbook(current_path + file_upload)
sheet = book.sheet_by_index(0)

error = False

print("=======START SCRIPT =========")
# sheet.nrows
# try:
for row_no in range(1, sheet.nrows):  #
    error = False
    row_values = sheet.row_values(row_no)
    prod_vals = {
        'isbn': row_values[1],
        'product_format': row_values[7],
        'origin': row_values[8],
        'weight': row_values[11],
    }
    prod_id = sock.execute(
        dbname, uid, password,
        'product.product',
        'search',
        [('default_code', '=', row_values[0])])
    print ("\n product>>>>>.", prod_id, row_values[0])
    if prod_id and prod_id[0]:
        prod_id = prod_id[0]
        prod_tmpl_id = sock.execute(
            dbname, uid, password,
            'product.product', 'read',
            prod_id, ['product_tmpl_id'])
        prod_tmpl_id = prod_tmpl_id and prod_tmpl_id[0] or 0
        if prod_tmpl_id:
            prod_tmpl_id = prod_tmpl_id.get('product_tmpl_id')[0]
        print ("\n prod_tmpl_id >>final>>>", prod_tmpl_id)
        publisher_id = sock.execute(
            dbname, uid, password,
            'res.partner',
            'search',
            [('name', 'ilike', row_values[3])])
        publisher_id = publisher_id and publisher_id[0] or False
        print ("\n publisher_id >>>>>>.", publisher_id)
        if not publisher_id:
            publisher_id = sock.execute(
                dbname, uid, password,
                'res.partner',
                'create',
                {'name': row_values[3], 'is_publisher': True})
            print ("\n crete >", publisher_id)
        if publisher_id:
            prod_vals.update({'publisher_id': publisher_id})
            sock.execute(
                dbname, uid, password,
                'res.partner',
                'write',
                publisher_id,
                {'is_publisher': True})
        author_id = sock.execute(
            dbname, uid, password,
            'res.partner',
            'search',
            [('name', 'ilike', row_values[6])])
        author_id = author_id and author_id[0] or False
        print ("\n author_id >>>>", author_id)
        if not author_id:
            author_id = sock.execute(
                dbname, uid, password,
                'res.partner',
                'create',
                {'name': row_values[6]})
            print ("\n not author_id >>>", author_id)
        if author_id:
            prod_vals.update({'author_id': author_id})
            sock.execute(
                dbname, uid, password,
                'res.partner',
                'write',
                author_id,
                {'is_author': True})
        sock.execute(
            dbname, uid, password,
            'product.template',
            'write',
            prod_tmpl_id,
            prod_vals)
        supplier_id = sock.execute(
            dbname, uid, password,
            'res.partner',
            'search',
            [('name', 'ilike', row_values[2])])
        supplier_id = supplier_id and supplier_id[0] or False
        if not supplier_id:
            supplier_id = sock.execute(
                dbname, uid, password,
                'res.partner',
                'create',
                {'name': row_values[2]})
            print ("\n not supported >>>", supplier_id)
        print ("\n supplier_id >>>", supplier_id)
        if supplier_id:
            vendor_price_list = sock.execute(
                dbname, uid, password,
                'product.supplierinfo',
                'search',
                [('name.id', '=', supplier_id),
                 ('product_tmpl_id', '=', prod_tmpl_id)])
            vendor_price_list = vendor_price_list and vendor_price_list[0]
            if vendor_price_list:
                cover_price = sock.execute(
                    dbname, uid, password,
                    'product.supplierinfo',
                    'read',
                    vendor_price_list,
                    ['price'])[0].get('price', 0)
                print ("\n cover_price >>>>>>>", cover_price)
                if not cover_price:
                    sock.execute(
                        dbname, uid, password,
                        'product.supplierinfo',
                        'write',
                        vendor_price_list,
                        {'price': row_values[5]})
                    print ("\n price >>>>>>", cover_price)
            if not vendor_price_list:
                print ("\n1 >>>>>>")
                price_vals = {
                    'name': supplier_id,
                    'product_id': prod_id,
                    'product_tmpl_id': prod_tmpl_id,
                    'price': row_values[5],
                }
                print ("\n price_vals >>>", price_vals)
                sock.execute(
                    dbname, uid, password,
                    'product.supplierinfo',
                    'create',
                    price_vals)
            print ("\n 2 >>>>>>>>")
# except Exception as e:
#     row_values.append(str(e))
#     output.write(str(row_values) + '\n')

# print("=======SCRIPT COMPLETE =========")
