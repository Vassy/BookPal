# -*- coding: utf-8 -*-
import base64
import binascii
import tempfile
import logging
import io
import re

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')
try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')


class ImportVendor(models.TransientModel):

    _name='import.vendor'
    _description = "Import Vendor"

    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='Select',default='csv')
    file_name = fields.Char(string="File Name")
    file = fields.Binary(string="Select File")

    def import_vendor(self):
        if self.import_option == 'xls':
            self.import_xls_vendor()
        if self.import_option == 'csv':
            self.import_csv_vendor()

    def import_csv_vendor(self):
        delivery_product_id = self.env.ref('bookpal_import.product_product_delivery')

        csv_data = base64.b64decode(self.file)
        data_file = io.StringIO(csv_data.decode("utf-8"))
        data_file.seek(0)
        file_reader = []
        csv_reader = csv.reader(data_file, delimiter=',')
        file_reader.extend(csv_reader)
        created_vendors = {}

        count = 0
        for row in file_reader:
            count += 1
            if count ==1:
                continue

            name = row[0]
            account_number = row[1]
            # main_address = row[2]
            # return_address = row[36]
            # warehouse_address = row[53]
            # warehouse_zip_code = row[54]

            default_shipping = row[14]
            delivery_carrier = self.env['delivery.carrier']
            if default_shipping:
                delivery_carrier = delivery_carrier.search([('name','=',default_shipping)], limit=1)
                if not delivery_carrier:
                    delivery_carrier = delivery_carrier.create({
                        'name':default_shipping,
                        'delivery_type': 'fixed',
                        'product_id': delivery_product_id.id,
                    })

            supplier_terms = row[48]
            account_pyment_term = self.env['account.payment.term']
            if supplier_terms:
                account_pyment_term = account_pyment_term.search([('name','=',supplier_terms)], limit=1)
                if not account_pyment_term:
                    account_pyment_term = account_pyment_term.create({
                        'name':supplier_terms
                    })

            vendor_vals = {
                'name': name,
                'account_number': account_number,
                'author_event_naunces': row[3],
                'author_event_shipping_naunces': row[4],
                'availability_check': row[5],
                'avg_discount': row[6],
                'avg_processing_time': row[7],
                'cc_email': row[8],
                'combine': True if row[9] in ['Yes', 'yes'] else False,
                'customer_service_email': row[10],
                'customer_service_hours': row[11],
                'customer_service_phone': row[12],
                'default_frieght_charges': row[13],
                'default_shipping_id': delivery_carrier.id,
                'discount_notes': row[15],
                'dropship_applicable': True if row[16] else False,
                'frieght_nuances': row[17],
                'future_ship_nuances': row[18],
                'intl_shipping_notes': row[19],
                'invoice_issues_contact': row[20],
                'minimums': True if row[21] in ['Yes', 'yes'] else False,
                'minimums_nuances': row[22],
                'non_conus_shipping': row[23],
                'comment': row[24],
                'note_to_vendor_nuances': row[25],
                'opening_text_nuances': row[26],
                'pre_approval_nuances': row[27],
                'price_match_discounts': row[28],
                'pricing_profile': row[29],
                'pricing_profile_notes': row[30],
                'processing_time_nuances': row[31],
                'publisher_nuances': row[32],
                'website': row[33],
                'rep': row[34],
                'returnable_terms': row[35],
                'rush_processing_time': row[38],
                'rush_processing_nuances': row[39],
                'shipping_acct_nuances': row[40],
                'shipping_notes': row[41],
                'shipping_nuances': row[42],
                'active': True if row[43] in ['Enabled', 'enabled'] else False,
                'supplier_discount': row[45],
                'email': row[46],
                'supplier_nuances': row[47],
                'property_supplier_payment_term_id': account_pyment_term.id,
                'top_publisher': True if row[49] else False,
                'tracking_souurce': row[50],
                'transfer_nuances': row[51],
                'transfer_to_bp_warehouse': True if row[52] else False,
            }

            partner_id = self.env['res.partner'].search([('name','=', name),('account_number','=',account_number)], limit=1)

            if partner_id:
                partner_id.write(vendor_vals)
            else:
                partner_id = partner_id.create(vendor_vals)

            # Supplier Contact
            supplier_contact = row[44]
            if supplier_contact:
                primary_contact_vals = {
                    'name': supplier_contact,
                    'parent_id': partner_id.id,
                    'is_primary': True,
                }
                primary_contact = self.env['res.partner'].search([
                    ('name', '=', supplier_contact),
                    ('parent_id', '=', partner_id.id)
                ], limit=1)
                if not primary_contact:
                    primary_contact.create(primary_contact_vals)
                else:
                    primary_contact.write(primary_contact_vals)

            _logger.warning("Contact : %s", name)

    def import_xls_vendor(self):
        try:
            fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
        except Exception:
            raise ValidationError(_("Invalid file!"))

        for row_no in range(sheet.nrows):
            val = {}
            if row_no == 0:
                continue
 
            line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
