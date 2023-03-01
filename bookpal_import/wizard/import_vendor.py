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
    _name = 'import.vendor'
    _description = "Import Vendor"

    import_option = fields.Selection([
        ('csv', 'CSV File'),
        # ('xls', 'XLS File')
    ], string='Select', default='csv')
    file_name = fields.Char(string="File Name")
    file = fields.Binary(string="Select File")

    def import_vendor(self):
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
        header_colunms = []

        count = 0
        for row in file_reader:
            count += 1
            if count == 1:
                header_colunms = row
                continue

            vals = self._prepare_dict_with_value(header_colunms, row)

            name = vals.get('Supplier: Supplier Name')
            account_number = vals.get('Account Number')

            default_shipping = vals.get('Default Shipping')
            delivery_carrier = self.env['delivery.carrier']
            if default_shipping:
                delivery_carrier = delivery_carrier.search([('name', '=', default_shipping)], limit=1)
                if not delivery_carrier:
                    delivery_carrier = delivery_carrier.create({
                        'name': default_shipping,
                        'delivery_type': 'fixed',
                        'product_id': delivery_product_id.id,
                    })

            supplier_terms = vals.get('Supplier Terms')
            account_pyment_term = self.env['account.payment.term']
            if supplier_terms:
                account_pyment_term = account_pyment_term.search([('name', '=', supplier_terms)], limit=1)
                if not account_pyment_term:
                    account_pyment_term = account_pyment_term.create({
                        'name': supplier_terms
                    })

            state_id = self.get_state(vals.get('Address:State'))

            vendor_vals = {
                'name': name,
                'account_number': account_number,
                'street': vals.get('Address:Street'),
                'street2': vals.get('Address:Street2'),
                'city': vals.get('Address:City'),
                'state_id': state_id.id,
                'zip': vals.get('Address:Zip'),
                'country_id': state_id.country_id.id,
                'author_event_naunces': vals.get('Author Event Nuances'),
                'author_event_shipping_naunces': vals.get('Author Event Shipping Nuances'),
                'availability_check': vals.get('Availability Check'),
                'avg_discount': vals.get('Average Discount %'),
                'avg_processing_time': vals.get('Average Processing Time'),
                'cc_email': vals.get('CC Email Addresses'),
                'combine': True if vals.get('Combine') in ['Yes', 'yes'] else False,
                'customer_service_email': vals.get('Customer Service Email'),
                'customer_service_hours': vals.get('Customer Service Hours'),
                'customer_service_phone': vals.get('Customer Service Phone'),
                'default_frieght_charges': vals.get('Default Freight Charge'),
                'default_shipping_id': delivery_carrier.id,
                'discount_notes': vals.get('Discount Notes'),
                'dropship_applicable': True if vals.get('Dropship') in ['1', 1] else False,
                'frieght_nuances': vals.get('Freight Nuances'),
                'future_ship_nuances': vals.get('Future Ship Nuances'),
                'intl_shipping_notes': vals.get("Int'l Shipping Notes"),
                'invoice_issues_contact': vals.get('Invoice Issues Contact'),
                'minimums': True if vals.get('Minimums') in ['Yes', 'yes'] else False,
                'minimums_nuances': vals.get('Minimums Nuances'),
                'non_conus_shipping': vals.get('Non-CONUS Shipping'),
                'comment': vals.get('Notes'),
                'note_to_vendor_nuances': vals.get('Note to Vendor Nuances'),
                'opening_text_nuances': vals.get('Opening Text Nuances'),
                'pre_approval_nuances': vals.get('Pre Approval Nuances'),
                'price_match_discounts': vals.get('Price Match Discounts'),
                'pricing_profile': vals.get('Pricing Profile'),
                'pricing_profile_notes': vals.get('Pricing Profile Notes'),
                'processing_time_nuances': vals.get('Processing Time Nuances'),
                'publisher_nuances': vals.get('Publisher Nuances'),
                'website': vals.get('Publisher Website'),
                # 'rep': vals.get('Rep'),
                'returnable_terms': vals.get('Returnable Terms'),
                'rush_processing_time': vals.get('Rush Processing Time'),
                'rush_processing_nuances': vals.get('Rush Shipping Nuances'),
                'shipping_acct_nuances': vals.get('Shipping Acct Nuances'),
                'shipping_notes': vals.get('Shipping Notes'),
                'shipping_nuances': vals.get('Shipping Nuances'),
                'active': True if vals.get('Status') in ['Enabled', 'enabled'] else False,
                'supplier_discount': vals.get('Supplier Discount (%)'),
                # 'email': vals.get('Supplier Email'),
                'supplier_nuances': vals.get('Supplier Nuances'),
                'property_supplier_payment_term_id': account_pyment_term.id,
                'top_publisher': True if vals.get('Top publisher') in ['1', 1] else False,
                'tracking_souurce': vals.get('Tracking Source'),
                'transfer_nuances': vals.get('Transfer Nuances'),
                'transfer_to_bp_warehouse': True if vals.get('Transfer to BookPal Warehouse') in ['1', 1] else False,
                'supplier_rank': 1,
            }

            partner_id = self.env['res.partner'].search([('name', '=', name), ('account_number', '=', account_number)],
                                                        limit=1)

            if partner_id:
                partner_id.write(vendor_vals)
            else:
                partner_id = partner_id.create(vendor_vals)

            # Supplier Contact
            supplier_contact = vals.get('Supplier Contact')
            if supplier_contact:
                primary_contact_vals = {
                    'name': supplier_contact,
                    'parent_id': partner_id.id,
                    'is_primary': True,
                    'email': vals.get('Supplier Email')
                }
                primary_contact = self.env['res.partner'].search([
                    ('name', '=', supplier_contact),
                    ('parent_id', '=', partner_id.id)
                ], limit=1)
                if not primary_contact:
                    primary_contact.create(primary_contact_vals)
                else:
                    primary_contact.write(primary_contact_vals)

            # Return Address
            return_address_street = vals.get('Returns Address:Street')
            if return_address_street:
                return_state_id = self.get_state(vals.get('Returns Address:State'))
                return_address_vals = {
                    'type': 'return',
                    'parent_id': partner_id.id,
                    'street': return_address_street,
                    'street2': vals.get('Returns Address:Street2'),
                    'city': vals.get('Returns Address:City'),
                    'state_id': return_state_id.id,
                    'zip': vals.get('Returns Address:Zip'),
                    'country_id': return_state_id.country_id.id,
                }
                return_address = self.env['res.partner'].search([
                    ('type', '=', 'return'),
                    ('street', '=', return_address_street),
                    ('parent_id', '=', partner_id.id)
                ], limit=1)
                if not return_address:
                    return_address.create(return_address_vals)
                else:
                    return_address.write(return_address_vals)

            # Warehouse Address
            warehouse_address_street = vals.get('Warehouse Address:Street')
            if warehouse_address_street:
                warehouse_state_id = self.get_state(vals.get('Warehouse Address:State'))
                wh_address_vals = {
                    'type': 'warehouse',
                    'parent_id': partner_id.id,
                    'street': warehouse_address_street,
                    'street2': vals.get('Warehouse Address:Street2'),
                    'city': vals.get('Warehouse Address:City'),
                    'state_id': warehouse_state_id.id,
                    'zip': vals.get('Warehouse Address:Zip'),
                    'country_id': warehouse_state_id.country_id.id,
                }
                wh_address = self.env['res.partner'].search([
                    ('type', '=', 'warehouse'),
                    ('street', '=', warehouse_address_street),
                    ('parent_id', '=', partner_id.id)
                ], limit=1)
                if not wh_address:
                    wh_address.create(wh_address_vals)
                else:
                    wh_address.write(wh_address_vals)

            _logger.info("Contact : %s", name)

    def _prepare_dict_with_value(self, header_colunms, row):
        vals = {}
        for key, value in zip(header_colunms, row):
            vals.update({key: value})
        return vals

    def get_state(self, state_name):
        state_id = self.env['res.country.state'].search([
            '|', ('code', '=', state_name),
            ('name', '=', state_name)
        ], limit=1)
        return state_id
