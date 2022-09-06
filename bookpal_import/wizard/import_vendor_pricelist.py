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

    _name='import.vendor.pricelist'
    _description = "Import Vendor Pricelist"

    import_option = fields.Selection([
            ('csv', 'CSV File'),
            # ('xls', 'XLS File')
        ], string='Select',default='csv')
    file_name = fields.Char(string="File Name")
    file = fields.Binary(string="Select File")

    def import_vendor_pricelist(self):
        if self.import_option == 'csv':
            self.import_csv_vendor_pricelist()

    def import_csv_vendor_pricelist(self):
        csv_data = base64.b64decode(self.file)
        data_file = io.StringIO(csv_data.decode("utf-8"))
        data_file.seek(0)
        file_reader = []
        csv_reader = csv.reader(data_file, delimiter=',')
        file_reader.extend(csv_reader)
        created_vendors = {}
        not_found_code_vendor = {}

        count = 0
        for row in file_reader:
            count += 1
            if count ==1:
                continue
            # if count == 100:
            #     break
            product_code = row[0]
            vendor_name = row[1]

            product_tmpl_id = self.env['product.template'].search([('default_code','=',product_code)], limit=1)
            partner_id = self.env['res.partner'].search([('name','=',vendor_name)], limit=1)

            commercial_partner_id = partner_id.commercial_partner_id

            if product_tmpl_id and partner_id:
                vendor_pricelist = self.env['product.supplierinfo'].search([
                    ('name','=',commercial_partner_id.id),
                    ('product_tmpl_id','=', product_tmpl_id.id)  
                ], limit=1)
                if not vendor_pricelist:
                    vendor_pricelist.create({
                        'name': commercial_partner_id.id,
                        'product_tmpl_id': product_tmpl_id.id,  
                    })
            else:
                not_found_code_vendor[product_code] = vendor_name
            _logger.info("Pricelist Code: %s", product_code)
        _logger.warning("Pricelist Not Created %s", not_found_code_vendor)
