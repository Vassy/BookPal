from odoo import fields, models, api
from requests import request
import logging
import json
from datetime import timedelta
import requests
import json
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from datetime import datetime
import time
import base64
from odoo.exceptions import UserError, ValidationError
from odoo.addons.product.models.product import ProductProduct
from odoo.addons.bigcommerce_odoo_integration.models.product_template import ProductTemplate

_logger = logging.getLogger("BigCommerce")

def import_product_from_bigcommerce(self, warehouse_id=False, bigcommerce_store_ids=False,
                                    bigcommerce_product_id=False, add_single_product=False, source_page=1,
                                    destination_page=1):
    for bigcommerce_store_id in bigcommerce_store_ids:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Auth-Client': '{}'.format(bigcommerce_store_ids.bigcommerce_x_auth_client),
            'X-Auth-Token': "{}".format(bigcommerce_store_ids.bigcommerce_x_auth_token)
        }
        req_data = False
        bigcommerce_store_id.bigcommerce_product_import_status = "Import Product Process Running..."
        product_process_message = "Process Completed Successfully!"
        operation_id = self.with_user(1).create_bigcommerce_operation('product', 'import', bigcommerce_store_id,
                                                                      'Processing...', warehouse_id)
        self._cr.commit()
        product_response_pages = []
        inven_location_id = self.env['stock.location'].search(
            [('name', '=', 'Inventory adjustment'), ('usage', '=', 'inventory')], limit=1)
        pricelist_obj = self.env['product.pricelist']
        pricelist_item_obj = self.env['product.pricelist.item']
        pricelist_id = pricelist_obj.search([('is_bigcommerce_pricelist', '=', True)])
        if not pricelist_id:
            pricelist_id = pricelist_obj.create({'bc_store_id': bigcommerce_store_id.id, 'is_bigcommerce_pricelist': True, 'name': 'Bigcommerce PriceList'})
        try:
            total_pages = 0
            if add_single_product:
                api_operation = "/v3/catalog/products/{}".format(bigcommerce_product_id)
                response_data = bigcommerce_store_id.with_user(1).send_get_request_from_odoo_to_bigcommerce(
                    api_operation)
            else:
                api_operation = "/v3/catalog/products"
                response_data = bigcommerce_store_id.with_user(1).send_get_request_from_odoo_to_bigcommerce(
                    api_operation)

            # _logger.info("BigCommerce Get Product  Response : {0}".format(response_data))
            product_ids = self.with_user(1).search([('bigcommerce_product_id', '=', False)])
            _logger.info("Response Status: {0}".format(response_data.status_code))
            if response_data.status_code in [200, 201]:
                response_data = response_data.json()
                total_pages = response_data.get('meta', {}).get('pagination', {}).get('total_pages', 0)
                # _logger.info("Product Response Data : {0}".format(response_data))
                records = response_data.get('data')
                location_id = bigcommerce_store_id.warehouse_id.lot_stock_id
                if add_single_product:
                    total_pages = 0
                else:
                    if total_pages > 0:
                        bc_total_pages = total_pages + 1
                        inp_from_page = source_page or bigcommerce_store_id.source_of_import_data
                        inp_total_pages = destination_page or bigcommerce_store_id.destination_of_import_data
                        from_page = bc_total_pages - inp_total_pages
                        total_pages = bc_total_pages - inp_from_page
                    else:
                        from_page = source_page or bigcommerce_store_id.source_of_import_data
                        total_pages = destination_page or bigcommerce_store_id.destination_of_import_data

                if total_pages > 1:
                    while (total_pages >= from_page):
                        try:
                            page_api = "/v3/catalog/products?page=%s" % (total_pages)
                            page_response_data = bigcommerce_store_id.send_get_request_from_odoo_to_bigcommerce(
                                page_api)
                            # _logger.info("Response Status: {0}".format(page_response_data.status_code))
                            if page_response_data.status_code in [200, 201]:
                                page_response_data = page_response_data.json()
                                _logger.info("Product Response Data : {0}".format(page_response_data))
                                records = page_response_data.get('data')
                                product_response_pages.append(records)
                        except Exception as e:
                            product_process_message = "Page is not imported! %s" % (e)
                            _logger.info("Getting an Error In Import Product Category Response {}".format(e))
                            process_message = "Getting an Error In Import Product Category Response {}".format(e)
                            self.with_user(1).create_bigcommerce_operation_detail('product', 'import',
                                                                                  response_data,
                                                                                  process_message, operation_id,
                                                                                  warehouse_id, True,
                                                                                  product_process_message)

                        total_pages = total_pages - 1
                else:
                    product_response_pages.append(records)
                location = location_id.ids + location_id.child_ids.ids

                product_ids_ls = []
                lot_stock_id = bigcommerce_store_id.warehouse_id.lot_stock_id
                for product_response_page in product_response_pages:
                    if add_single_product:
                        product_response_page = [records]
                    for record in product_response_page:
                        try:
                            product_template_id = False
                            bc_product_id = record.get('id')
                            listing_id = self.env['bc.store.listing'].search(
                                [('bc_product_id', '=', record.get('id')),
                                 ('bigcommerce_store_id', '=', bigcommerce_store_id.id)])
                            if listing_id:
                                product_template_id = listing_id.product_tmpl_id
                                _logger.info("::: Listing is already created {}".format(listing_id.id))
                                # continue
                            if not product_template_id:
                                if bigcommerce_store_id.bigcommerce_product_skucode and record.get('sku'):
                                    product_template_id = self.env['product.template'].sudo().search(
                                        [('default_code', '=', record.get('sku'))], limit=1)
                            if not product_template_id:
                                product_template_id = self.env['product.template'].sudo().search(
                                    [('name', '=', record.get('name'))], limit=1)
                            if not product_template_id:
                                status, product_template_id = self.with_user(1).create_product_template(record,
                                                                                                        bigcommerce_store_id)
                                if not status:
                                    product_process_message = "%s : Product is not imported Yet! %s" % (
                                        record.get('id'), product_template_id)
                                    _logger.info("Getting an Error In Import Product Responase :{}".format(
                                        product_template_id))
                                    self.with_user(1).create_bigcommerce_operation_detail('product', 'import', "",
                                                                                          "", operation_id,
                                                                                          warehouse_id, True,
                                                                                          product_process_message)
                                    continue
                                process_message = "Product Created : {}".format(product_template_id.name)
                                _logger.info("{0}".format(process_message))
                                response_data = record
                                self.with_user(1).create_bigcommerce_operation_detail('product', 'import', req_data,
                                                                                      response_data, operation_id,
                                                                                      warehouse_id, False,
                                                                                      process_message)
                                self._cr.commit()
                            else:
                                process_message = "{0} : Product Already Exist In Odoo!".format(
                                    product_template_id.name)
                                brand_id = self.env['bc.product.brand'].sudo().search(
                                    [('bc_brand_id', '=', record.get('brand_id'))], limit=1)
                                _logger.info("BRAND : {0}".format(brand_id))
                                public_category_ids = self.env['product.category'].sudo().search(
                                    [('bigcommerce_product_category_id', 'in', record.get('categories'))])
                                product_template_id.write({
                                    "list_price": record.get("price"),
                                    "standard_price": record.get("cost_price"),
                                    "is_visible": record.get("is_visible"),
                                    "inventory_tracking": record.get("inventory_tracking"),
                                    "bigcommerce_product_id": record.get('id'),
                                    "bigcommerce_store_id": bigcommerce_store_id.id,
                                    "public_categories_ids": [(6, 0, public_category_ids.ids)],
                                    "default_code": record.get("sku"),
                                    "is_imported_from_bigcommerce": True,
                                    "description_sale": "",
                                    "description": record.get('description'),
                                    "is_exported_to_bigcommerce": True,
                                    "x_studio_manufacturer": brand_id and brand_id.id,
                                    "name": record.get('name'),
                                    "property_stock_inventory": inven_location_id.id
                                })
                                self.with_user(1).create_bigcommerce_operation_detail('product', 'import', req_data,
                                                                                      response_data, operation_id,
                                                                                      warehouse_id, False,
                                                                                      process_message)
                                _logger.info("{0}".format(process_message))
                                self._cr.commit()
                            self.env['product.attribute'].import_product_attribute_from_bigcommerce(warehouse_id,
                                                                                                    bigcommerce_store_id,
                                                                                                    product_template_id,
                                                                                                    operation_id)

                            if not listing_id:
                                listing_id = self.env['bc.store.listing'].create_or_update_bc_store_listing(record,
                                                                                                            product_template_id,
                                                                                                            bigcommerce_store_id)
                            self.env['bigcommerce.product.image'].with_user(1).import_multiple_product_image(
                                bigcommerce_store_id, product_template_id, listing_id)
                            try:
                                bulk_pricing_rule_api_operation = '/v3/catalog/products/{0}/bulk-pricing-rules'.format(listing_id.bc_product_id)
                                pricerule_response_data = bigcommerce_store_id.send_get_request_from_odoo_to_bigcommerce(bulk_pricing_rule_api_operation)
                                if pricerule_response_data.status_code in [200, 201]:
                                    pricerule_response_data = pricerule_response_data.json()
                                    if len(pricerule_response_data.get('data')) > 1:
                                        _logger.info("Price Rule Response Data : {0}".format(pricerule_response_data))
                                        for rule in pricerule_response_data.get('data'):
                                            if rule.get('type') == 'percent':
                                                compute_price = 'percentage'
                                                vals = {'applied_on': '1_product',
                                                        'priceing_rule_id': rule.get('id'),
                                                        'product_tmpl_id': listing_id.product_tmpl_id.id,
                                                        'min_quantity': float(rule.get('quantity_min')),
                                                        'compute_price': compute_price,
                                                        'percent_price':float(rule.get('amount')),
                                                        'pricelist_id':pricelist_id.id}
                                            elif rule.get('type') == 'price':
                                                compute_price = 'fixed'
                                                vals = {'applied_on': '1_product',
                                                        'priceing_rule_id':rule.get('id'),
                                                        'product_tmpl_id': listing_id.product_tmpl_id.id,
                                                        'min_quantity': float(rule.get('quantity_min')),
                                                        'compute_price': compute_price,
                                                        'fixed_price': float(rule.get('amount')),
                                                        'pricelist_id':pricelist_id.id}
                                            pricelist_item_id = pricelist_item_obj.search(
                                                [('priceing_rule_id', '=', rule.get('id')), (
                                                    'product_tmpl_id', '=', listing_id.product_tmpl_id.id), (
                                                     'min_quantity', '=',
                                                     float(rule.get('quantity_min')))])
                                            if not pricelist_item_id:
                                                pricelist_item_id = pricelist_item_obj.create(vals)
                                            else:
                                                pricelist_item_id.write(vals)
                            except Exception as e:
                                product_process_message = "Getting An Issue While Import Bulk Priceing Rule %s" % (e)
                                _logger.info("Getting An Issue While Import Bulk Priceing Rule {}".format(e))
                                process_message = "Getting An Issue While Import Bulk Priceing Rule {}".format(e)
                                self.with_user(1).create_bigcommerce_operation_detail('product', 'import',
                                                                                      response_data,
                                                                                      process_message, operation_id,
                                                                                      warehouse_id, True,
                                                                                      product_process_message)
                            if product_template_id.product_variant_count > 1:
                                api_operation_variant = "/v3/catalog/products/{}/variants".format(
                                    product_template_id.bigcommerce_product_id)
                                variant_response_data = bigcommerce_store_id.with_user(
                                    1).send_get_request_from_odoo_to_bigcommerce(api_operation_variant)
                                _logger.info(
                                    "BigCommerce Get Product Variant Response : {0}".format(variant_response_data))
                                _logger.info(
                                    "Response Status: {0}".format(variant_response_data.status_code))
                                if variant_response_data.status_code in [200, 201]:
                                    api_operation_variant_response_data = variant_response_data.json()
                                    variant_datas = api_operation_variant_response_data.get('data')
                                    for variant_data in variant_datas:
                                        option_labales = []
                                        option_values = variant_data.get('option_values')
                                        for option_value in option_values:
                                            option_labales.append(option_value.get('label'))
                                        v_id = variant_data.get('id')
                                        product_sku = variant_data.get('sku')
                                        _logger.info("Total Product Variant : {0} Option Label : {1}".format(
                                            product_template_id.product_variant_ids, option_labales))
                                        for product_variant_id in product_template_id.product_variant_ids:
                                            if product_variant_id.mapped(lambda pv: pv.with_user(
                                                    1).product_template_attribute_value_ids.mapped('name') == option_labales)[0]:
                                                _logger.info(
                                                    "Inside If Condition option Label =====> {0} Product Template "
                                                    "Attribute Value ====> {1} variant_id====>{2}".format(
                                                        option_labales, product_variant_id.with_user(1).mapped(
                                                            'product_template_attribute_value_ids').mapped('name'),
                                                        product_variant_id))
                                                if variant_data.get('price'):
                                                    price = variant_data.get('price')
                                                else:
                                                    price = variant_data.get('calculated_price')
                                                vals = {'default_code': product_sku, 'bc_sale_price': price,
                                                        'bigcommerce_product_variant_id': v_id,
                                                        'standard_price': variant_data.get('cost_price', 0.0)}
                                                variant_product_img_url = variant_data.get('image_url')
                                                if variant_product_img_url:
                                                    image = base64.b64encode(
                                                        requests.get(variant_product_img_url).content)
                                                    vals.update({'image_1920': image})
                                                product_variant_id.with_user(1).write(vals)
                                                _logger.info("Product Variant Updated : {0}".format(
                                                    product_variant_id.default_code))
                                                product_qty = variant_data.get('inventory_level')
                                                listing_item_id = self.env['bc.store.listing.item'].search(
                                                    [('bc_product_id', '=', variant_data.get('id')),
                                                     ('bigcommerce_store_id', '=', bigcommerce_store_id.id)])
                                                if not listing_item_id:
                                                    self.env[
                                                        'bc.store.listing.item'].create_or_update_bc_store_listing_item(
                                                        record, variant_data, product_template_id,
                                                        bigcommerce_store_id, listing_id, product_variant_id)
                                                self._cr.commit()

                                else:
                                    api_operation_variant_response_data = variant_response_data.json()
                                    error_msg = api_operation_variant_response_data.get('errors')
                                    self.create_bigcommerce_operation_detail('product_attribute', 'import', '',
                                                                             error_msg, operation_id, warehouse_id,
                                                                             True, error_msg)

                            self._cr.commit()
                        except Exception as e:
                            product_process_message = "%s : Product is not imported Yet! %s" % (record.get('id'), e)
                            _logger.info("Getting an Error In Import Product Responase".format(e))
                            self.with_user(1).create_bigcommerce_operation_detail('product', 'import', "",
                                                                                  "", operation_id,
                                                                                  warehouse_id, True,
                                                                                  product_process_message)
                operation_id and operation_id.with_user(1).write({'bigcommerce_message': product_process_message})
                _logger.info("Import Product Process Completed ")
            else:
                process_message = "Getting an Error In Import Product Responase : {0}".format(response_data)
                _logger.info("Getting an Error In Import Product Responase".format(response_data))
                self.with_user(1).create_bigcommerce_operation_detail('product', 'import', req_data, response_data,
                                                                      operation_id, warehouse_id, True, )
        except Exception as e:
            product_process_message = "Process Is Not Completed Yet! %s" % (e)
            _logger.info("Getting an Error In Import Product Responase".format(e))
            self.with_user(1).create_bigcommerce_operation_detail('product', 'import', "", "", operation_id,
                                                                  warehouse_id, True, product_process_message)
        bigcommerce_store_id.bigcommerce_product_import_status = "Import Product Process Completed."
        # product_process_message = product_process_message + "From :" + from_page +"To :" + total_pages
        operation_id and operation_id.with_user(1).write({'bigcommerce_message': product_process_message})
        self._cr.commit()

ProductTemplate.import_product_from_bigcommerce = import_product_from_bigcommerce

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def create_or_update_product_pricelist(self,bigcommerce_store_id,product_tmpl_ids):
        pricelist_obj = self.env['product.pricelist']
        pricelist_item_obj = self.env['product.pricelist.item']
        pricelist_id = pricelist_obj.search([('is_bigcommerce_pricelist', '=', True)])
        if not pricelist_id:
            pricelist_id = pricelist_obj.create(
                {'bc_store_id': bigcommerce_store_id.id, 'is_bigcommerce_pricelist': True,
                 'name': 'Bigcommerce PriceList'})
        for product_tmpl_id in product_tmpl_ids:
            bulk_pricing_rule_api_operation = '/v3/catalog/products/{0}/bulk-pricing-rules'.format(product_tmpl_id.bigcommerce_product_id)
            pricerule_response_data = bigcommerce_store_id.send_get_request_from_odoo_to_bigcommerce(bulk_pricing_rule_api_operation)
            if pricerule_response_data.status_code in [200, 201]:
                pricerule_response_data = pricerule_response_data.json()
                if len(pricerule_response_data.get('data')) > 1:
                    _logger.info("Price Rule Response Data : {0}".format(pricerule_response_data))
                    for rule in pricerule_response_data.get('data'):
                        if rule.get('type') == 'percent':
                            compute_price = 'percentage'
                            vals = {'applied_on': '1_product',
                                    'priceing_rule_id': rule.get('id'),
                                    'product_tmpl_id': product_tmpl_id.id,
                                    'min_quantity': float(rule.get('quantity_min')),
                                    'compute_price': compute_price,
                                    'percent_price': float(rule.get('amount')),
                                    'pricelist_id': pricelist_id.id}
                        elif rule.get('type') == 'price':
                            compute_price = 'fixed'
                            vals = {'applied_on': '1_product',
                                    'priceing_rule_id': rule.get('id'),
                                    'product_tmpl_id': product_tmpl_id.id,
                                    'min_quantity': float(rule.get('quantity_min')),
                                    'compute_price': compute_price,
                                    'fixed_price': float(rule.get('amount')),
                                    'pricelist_id': pricelist_id.id}
                        pricelist_item_id = pricelist_item_obj.search(
                            [('priceing_rule_id', '=', rule.get('id')), (
                                'product_tmpl_id', '=', product_tmpl_id.id), (
                                 'min_quantity', '=',
                                 float(rule.get('quantity_min')))])
                        if not pricelist_item_id:
                            pricelist_item_id = pricelist_item_obj.create(vals)
                        else:
                            pricelist_item_id.write(vals)
