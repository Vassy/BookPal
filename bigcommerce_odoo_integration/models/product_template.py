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

_logger = logging.getLogger("BigCommerce")

class ProductTemplate(models.Model):
    _inherit = "product.template"

    public_categories_ids = fields.Many2many('product.category', string='Product Categories')
    bigcommerce_product_image_ids = fields.One2many('bigcommerce.product.image', 'product_template_id',
                                                    string="Bigcommerce Product Image Ids")
    bigcommerce_product_id = fields.Char(string='Bigcommerce Product', copy=False)
    bigcommerce_store_id = fields.Many2one('bigcommerce.store.configuration', string="Bigcommerce Store", copy=False)
    is_exported_to_bigcommerce = fields.Boolean(string="Is Exported to Big Commerce ?", copy=False)
    inventory_tracking = fields.Selection([
        ('none', 'Inventory Level will not be tracked'),
        ('product', 'Inventory Level Tracked using the Inventory Level'),
        ('variant', 'Inventory Level Tracked Based on variant')
    ], default="none")
    inventory_warning_level = fields.Integer(string="Inventory Warning Level", copy=False)
    is_visible = fields.Boolean(string="Product Should Be Visible to Customer", default=True, copy=False)
    warranty = fields.Char(string="Warranty Information")
    is_imported_from_bigcommerce = fields.Boolean(string="Is Imported From Big Commerce ?", copy=False)
    x_studio_manufacturer = fields.Many2one('bc.product.brand', string='Manufacturer')
    bc_product_image_id = fields.Char(string='BC Product Image', copy=False)

    def unlink(self):
        """
        delete bigcommerce product listing on product template delete.
        """
        for record in self:
            listing = self.env['bc.store.listing'].search([('product_tmpl_id', '=', record.id)])
            if listing:
                listing.unlink()
        return super(ProductTemplate, self).unlink()

    def create_bigcommerce_operation(self, operation, operation_type, bigcommerce_store_id, log_message, warehouse_id):
        vals = {
            'bigcommerce_operation': operation,
            'bigcommerce_operation_type': operation_type,
            'bigcommerce_store': bigcommerce_store_id and bigcommerce_store_id.id,
            'bigcommerce_message': log_message,
            'warehouse_id': warehouse_id and warehouse_id.id or False
        }
        operation_id = self.env['bigcommerce.operation'].create(vals)
        return operation_id

    def create_bigcommerce_operation_detail(self, operation, operation_type, req_data, response_data, operation_id,
                                            warehouse_id=False, fault_operation=False, process_message=False):
        bigcommerce_operation_details_obj = self.env['bigcommerce.operation.details']
        vals = {
            'bigcommerce_operation': operation,
            'bigcommerce_operation_type': operation_type,
            'bigcommerce_request_message': '{}'.format(req_data),
            'bigcommerce_response_message': '{}'.format(response_data),
            'operation_id': operation_id.id,
            'warehouse_id': warehouse_id and warehouse_id.id or False,
            'fault_operation': fault_operation,
            'process_message': process_message
        }
        operation_detail_id = bigcommerce_operation_details_obj.create(vals)
        return operation_detail_id

    def product_request_data(self, product_id, warehouse_id):
        """
        Description : Prepare Product Request Data For Generate/Create Product in Bigcomeerce
        """
        product_variants = []
        product_name = product_id and product_id.name
        product_data = {
            "name": product_id.name,
            "price": product_id.list_price,
            "categories": [int(product_id.categ_id and product_id.categ_id.bigcommerce_product_category_id)],
            "weight": product_id.weight or 1.0,
            "type": "physical",
            "sku": product_id.default_code or '',
            "description": product_id.name,
            "cost_price": product_id.standard_price,
            "inventory_tracking": product_id.inventory_tracking,
            "inventory_level": product_id.with_context(warehouse=warehouse_id.id).qty_available,
            "is_visible": product_id.is_visible,
            "warranty": product_id.warranty or ''
        }
        return product_data

    def product_variant_request_data(self, product_variant):
        """
        Description : Prepare Product Variant Request Data For Create Product  Variant in Bigcommerce.
        """
        option_values = []
        product_data = {
            "cost_price": product_variant.standard_price,
            "price": product_variant.lst_price,
            "weight": product_variant.weight or 1.0,
            "sku": product_variant.default_code or '',
            "product_id": product_variant.product_tmpl_id.bigcommerce_product_id

        }
        for attribute_value in product_variant.attribute_value_ids:
            option_values.append({'id': attribute_value.bigcommerce_value_id,
                                  'option_id': attribute_value.attribute_id.bigcommerce_attribute_id})
        product_data.update({"option_values": option_values})
        return product_data

    def create_product_template(self, record, store_id):
        product_attribute_obj = self.env['product.attribute']
        product_attribute_value_obj = self.env['product.attribute.value']
        product_template_obj = self.env['product.template']
        template_title = ''
        if record.get('name', ''):
            template_title = record.get('name')
        attrib_line_vals = []
        _logger.info("{}".format(record.get('categories')))
        if record.get('variants'):
            for attrib in record.get('variants'):
                if not attrib.get('option_values'):
                    continue
                attrib_name = attrib.get('option_display_name')
                attrib_values = attrib.get('label')
                attribute = product_attribute_obj.get_product_attribute(attrib_name, type='radio',
                                                                        create_variant='always')
                attribute_val_ids = []

                attrib_value = product_attribute_value_obj.get_product_attribute_values(attrib_values, attribute.id)
                attribute_val_ids.append(attrib_value.id)

                if attribute_val_ids:
                    attribute_line_ids_data = [0, False, {'attribute_id': attribute.id,
                                                          'value_ids': [[6, False, attribute_val_ids]]}]
                    attrib_line_vals.append(attribute_line_ids_data)
        category_id = self.env['product.category'].sudo().search([('bigcommerce_product_category_id','in',record.get('categories'))],limit=1)
        if not category_id:
            category_id = self.env.ref('product.product_category_all')
        if not category_id:
            message = "Category not found!"
            _logger.info("Category not found: {}".format(category_id))
            return False, message
        public_category_ids = self.env['product.category'].sudo().search(
            [('bigcommerce_product_category_id', 'in', record.get('categories'))])
        brand_id = self.env['bc.product.brand'].sudo().search([('bc_brand_id', '=', record.get('brand_id'))], limit=1)
        _logger.info("BRAND : {0}".format(brand_id))
        inven_location_id = self.env['stock.location'].search(
            [('name', '=', 'Inventory adjustment'), ('usage', '=', 'inventory')], limit=1)
        vals = {
            'name': template_title,
            'type': 'product',
            'categ_id': category_id and category_id.id,
            "weight": record.get("weight"),
            "list_price": record.get("price"),
            "standard_price":record.get('cost_price'),
            "is_visible": record.get("is_visible"),
            "public_categories_ids": [(6, 0, public_category_ids.ids)],
            "bigcommerce_product_id": record.get('id'),
            "bigcommerce_store_id": store_id.id,
            "default_code": record.get("sku"),
            "is_imported_from_bigcommerce": True,
            "x_studio_manufacturer": brand_id and brand_id.id,
            "description_sale": "",
            "description": record.get('description'),
            "property_stock_inventory": inven_location_id.id
        }
        product_template = product_template_obj.with_user(1).create(vals)
        _logger.info("Product Created: {}".format(product_template))
        return True, product_template

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
                                    #continue
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
                                custom_field_api_operation = "v3/catalog/products/{}/custom-fields".format(
                                    record.get('id'))
                                custom_field_response_data = bigcommerce_store_id.with_user(
                                    1).send_get_request_from_odoo_to_bigcommerce(custom_field_api_operation)
                                _logger.info("Custom Field Response : {0}".format(custom_field_response_data))
                                if custom_field_response_data.status_code in [200, 201]:
                                    custom_field_response_data = custom_field_response_data.json()
                                    custom_field_datas = custom_field_response_data.get('data')
                                    for custom_field_data in custom_field_datas:
                                        if custom_field_data.get('name') in ['publisher', 'Publisher']:
                                            product_template_id.publisher_id = custom_field_data.get('value')
                                        elif custom_field_data.get('name') in ['supplier', 'Supplier']:
                                            product_template_id.supplier = custom_field_data.get('value')
                                        elif custom_field_data.get('name') in ['Publication Date', 'publication date']:
                                            product_template_id.publication_date = custom_field_data.get('value')
                                        elif custom_field_data.get('name') in ['pricing profile', 'Pricing Profile']:
                                            product_template_id.pricing_profile = custom_field_data.get('value')
                                        elif custom_field_data.get('name') in ['Special Title', 'special title']:
                                            product_template_id.special_title = custom_field_data.get('value')
                                        elif custom_field_data.get('name') in ['full title', 'Full Title']:
                                            product_template_id.full_title = custom_field_data.get('value')
                                        elif custom_field_data.get('name') in ['Short Title', 'short title']:
                                            product_template_id.short_title = custom_field_data.get('value')
                                        elif custom_field_data.get('name') in ['Format']:
                                            product_template_id.product_format = custom_field_data.get('value')
                                        elif custom_field_data.get('name') in ['Author','author']:
                                            product_template_id.author_ids = custom_field_data.get('value')
                                else:
                                    api_operation_custom_field_response_data = custom_field_response_data.json()
                                    error_msg = api_operation_custom_field_response_data.get('errors')
                                    self.create_bigcommerce_operation_detail('product', 'import', '',
                                                                             error_msg, operation_id, warehouse_id,
                                                                             True, error_msg)
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
                                                        1).product_template_attribute_value_ids.mapped(
                                                        'name') == option_labales)[0]:
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

    def update_product_variant_data_odoo_to_bc(self, product_id, bc_listing_id, bigcommerce_store_id, operation_id):
        if len(product_id.product_variant_ids) > 1:
            for product_variant_id in product_id.product_variant_ids:
                bc_listing_item_id = self.env['bc.store.listing.item'].search(
                    [('product_id', '=', product_variant_id.id),
                     ('bc_listing_id', '=', bc_listing_id.id),
                     ('bigcommerce_store_id', '=', bigcommerce_store_id.id)])
                if bc_listing_item_id:
                    variant_data = {
                        'sale_price': product_variant_id.lst_price,
                        'sku': product_variant_id.default_code or ''
                    }
                    api_operation = "/v3/catalog/products/{}/variants/{}".format(bc_listing_id.bc_product_id, bc_listing_item_id.bc_product_id)
                    _logger.info("Product Data : {}".format(variant_data))
                    response_data = bigcommerce_store_id.update_request_from_odoo_to_bigcommerce(variant_data,
                                                                                                 api_operation)
                    if response_data.status_code in [200, 201]:
                        bc_listing_item_id.update({'item_update_date': datetime.now(),
                                                   'default_code': product_variant_id.default_code or '',
                                                   'sale_price': product_variant_id.lst_price})
                    else:
                        _logger.info("Getting an Error Update Product Variant >>>>> {0} >>>>> Response: {1}".format(product_variant_id.display_name, response_data.json()))
                        self.sudo().create_bigcommerce_operation_detail('product', 'update', variant_data,
                                                                        response_data.json(),
                                                                        operation_id, bigcommerce_store_id.warehouse_id,
                                                                        True, "we couldn't update product variant - {}".format(product_variant_id.display_name))


    def request_export_update_product_data(self, product_id, bigcommerce_store_id, warehouse_id):
        categ_ids = []
        variants = []
        data = {
            "type": "physical",
            "weight": product_id.weight or 1.0,
            "is_visible": product_id.is_visible
        }
        ecomm_categ = product_id.public_categories_ids.mapped('bigcommerce_product_category_id')
        for categ_id in ecomm_categ:
            categ_ids.append(int(categ_id))
        if not ecomm_categ and product_id.categ_id.bigcommerce_product_category_id:
            categ_ids.append(int(product_id.categ_id.bigcommerce_product_category_id))
        data.update({
            "name": product_id.name,
            'price': str(product_id.list_price),
            "categories": categ_ids,
            "inventory_tracking": 'product',
            "inventory_level": int(product_id.with_context(warehouse=warehouse_id.id).qty_available),
            "sku": product_id.default_code or '',
            "description": product_id.description or '',
        })
        if len(product_id.product_variant_ids) > 1 and not self._context.get('do_not_add_variant'):
            for product_variant_id in product_id.product_variant_ids:
                option_values = []
                self._cr.execute(
                    "select product_template_attribute_value_id from product_variant_combination where product_product_id={}".format(
                        product_variant_id.id))
                prt_attribute_value_ids = self.env['product.template.attribute.value'].browse(
                    [row[0] for row in self._cr.fetchall()])
                template_attrib_value_ids = self.env['product.template.attribute.value'].search(
                    [('id', 'in', prt_attribute_value_ids.ids)])
                for tmpl in template_attrib_value_ids:
                    attribute_id = self.env['product.attribute'].search([('id', '=', tmpl.attribute_id.id)])
                    attribute_value_id = self.env['product.attribute.value'].search(
                        [('id', '=', tmpl.product_attribute_value_id.id)])
                    option_values.append({'option_display_name': attribute_id.name, 'label': attribute_value_id.name})
                variants.append({'sku': product_variant_id.default_code or '', 'option_values': option_values,
                                 'price': product_variant_id.lst_price})
            data.update({'variants': variants})
        return data

    def export_product_in_bigcommerce_from_product(self, bigcommerce_store_id, product_ids):
        operation_id = self.sudo().create_bigcommerce_operation('product', 'export', bigcommerce_store_id,
                                                                'Processing...',
                                                                bigcommerce_store_id.warehouse_id)
        for product in product_ids:
            try:
                images = []
                product_data = False
                check_listing_bc_product_id = self.env['bc.store.listing'].search(
                    [('product_tmpl_id', '=', product.id), ('bigcommerce_store_id', '=', bigcommerce_store_id.id)])
                if check_listing_bc_product_id:
                    _logger.info("PRODUCT IS ALREADY LISTED IN STORE : {0}".format(bigcommerce_store_id.name))
                    continue
                api_operation = "/v3/catalog/products"
                product_data = self.request_export_update_product_data(product, bigcommerce_store_id,
                                                                       bigcommerce_store_id.warehouse_id)
                _logger.info("EXPORT PRODUCT DATA : {0}".format(product_data))
                web_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                if product.image_1920:
                    product_standard_image_url = web_base_url + '/web/image/product.product/{}/image_1024/'.format(
                        product.product_variant_id.id)
                    product_tiny_image_url = web_base_url + '/web/image/product.product/{}/image_256/'.format(
                        product.product_variant_id.id)
                    images.append({'image_url': product_standard_image_url, 'is_thumbnail': True,
                                   'url_standard': product_standard_image_url, 'url_tiny': product_tiny_image_url,
                                   'description': 'Main Image' + ":" + str(product.id)})
                # for product_image_id in product.product_template_image_ids:
                #     media_standard_image_url = web_base_url + '/web/image/product.image/{}/image_1024/'.format(
                #         product_image_id.id)
                #     media_tiny_image_url = web_base_url + '/web/image/product.image/{}/image_256/'.format(
                #         product_image_id.id)
                #     images.append({'image_url': media_standard_image_url, 'is_thumbnail': False,
                #                    'url_standard': media_standard_image_url, 'url_tiny': media_tiny_image_url,
                #                    'description': product_image_id.name + ":" + str(product_image_id.id)})
                product_data.update({'images': images})
                response_data = bigcommerce_store_id.send_request_from_odoo_to_bigcommerce(product_data,
                                                                                           api_operation)
                response = response_data.json()

                if response_data.status_code in [200, 201]:
                    bc_product_id = response.get('data') and response.get('data').get('id')
                    variants = response.get('data') and response.get('data').get('variants') or []
                    product_data.update({'id': bc_product_id})
                    listing_id = self.env['bc.store.listing'].create_or_update_bc_store_listing(product_data,
                                                                                                product,
                                                                                                bigcommerce_store_id)
                    all_images = response.get('data') and response.get('data').get('images')
                    for img in all_images:
                        bc_pro_img_obj = self.env['bigcommerce.product.image']
                        values = {
                            'bigcommerce_product_image_id': img.get('id'),
                            'bigcommerce_product_image': base64.b64encode(
                                requests.get(img.get('url_standard')).content),
                            'bigcommerce_product_id': img.get('product_id'),
                            'bigcommerce_listing_id': listing_id.id,
                            'bigcommerce_store_id': bigcommerce_store_id.id,
                            'name': img.get('image_file')
                        }
                        if img.get('is_thumbnail'):
                            listing_id.image_1920 = base64.b64encode(requests.get(img.get('url_standard')).content)
                            listing_id.bc_product_image_id = img.get('id')
                            continue
                        if not bc_pro_img_obj.search([('bigcommerce_product_image_id', '=', img.get('id'))]):
                            bc_pro_img_obj.create(values)
                        else:
                            bc_pro_img_obj.write(values)
                    for variant_dict in variants:
                        product_id = self.env['product.product'].search(
                            [('default_code', '=', variant_dict.get('sku'))])
                        product_id.bigcommerce_product_variant_id = variant_dict.get('id')
                        self.env['bc.store.listing.item'].create_or_update_bc_store_listing_item(
                            product_data, variant_dict, product,
                            bigcommerce_store_id, listing_id, product_id)
                    images = response.get('data') and response.get('data').get('images')
                    for image in images:
                        product_image_desc = image.get('description')
                        product_image_desc = product_image_desc.split(':')
                        if 'Main Image' in product_image_desc:
                            product.bc_product_image_id = image.get('id')
                            listing_id.bc_product_image_id = image.get('id')
                        # else:
                        #     ecom_product_image_id = self.env['product.image'].search(
                        #         [('id', '=', product_image_desc[1])])
                        #     ecom_product_image_id.bc_product_image_id = image.get('id')
                    product.write({'bigcommerce_product_id': bc_product_id, 'is_exported_to_bigcommerce': True})
                    process_message = "Product Exported Successfully : {0} BC Product ID : {1}".format(product.name,
                                                                                                      bc_product_id)
                    self.sudo().create_bigcommerce_operation_detail('product', 'export', product_data, response,
                                                                    operation_id, bigcommerce_store_id.warehouse_id,
                                                                    False, process_message)
                    self._cr.commit()
                else:
                    error_message = response.get('errors')
                    self.sudo().create_bigcommerce_operation_detail('product', 'export', product_data, response,
                                                                    operation_id, bigcommerce_store_id.warehouse_id,
                                                                    True, error_message)
                    _logger.info(
                        "Getting an Error Product >>>>> {0} >>>>> Response: {1}".format(product.name, response_data))
                operation_id.bigcommerce_message = 'process completed'
            except Exception as e:
                process_message = "Getting an Error In Export Product Response:{0}".format(e)
                _logger.info("Getting an Error In Export Product Response:{0}".format(e))
                self.sudo().create_bigcommerce_operation_detail('product', 'export', product_data, response,
                                                                operation_id,
                                                                bigcommerce_store_id.warehouse_id, False,
                                                                process_message)
                operation_id.bigcommerce_message = 'getting an error'

    def update_product_in_bigcommerce_from_product(self, bigcommerce_store_id, product_ids):
        try:
            # product_data = []
            # count = 1
            image_dict = {}
            operation_id = self.sudo().create_bigcommerce_operation('product', 'update', bigcommerce_store_id,
                                                                    'Processing...',
                                                                    bigcommerce_store_id.warehouse_id)

            # product_ids = self.search([('bigcommerce_product_id', '!=', False)], order='id')
            web_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            count = 0
            for product in product_ids:
                count += 1
                bc_listing_id = self.env['bc.store.listing'].search(
                    [('product_tmpl_id', '=', product.id), ('bigcommerce_store_id', '=', bigcommerce_store_id.id)])
                if not bc_listing_id:
                    _logger.info("PRODUCT IS NOT LISTED IN STORE : {0}".format(bigcommerce_store_id.name))
                    continue
                images = []
                if bc_listing_id.image_1920:
                    product_standard_image_url = web_base_url + '/web/image/bc.store.listing/{}/image_1920/'.format(
                        bc_listing_id.id)
                    image_dict = {'image_url': product_standard_image_url, 'is_thumbnail': True,
                                  'url_standard': product_standard_image_url, 'url_tiny': product_standard_image_url,
                                  'description': 'Main Image' + ":" + str(bc_listing_id.id)}
                bc_product_id = bc_listing_id.bc_product_id
                bc_product_main_image_id = bc_listing_id.bc_product_image_id
                if bc_product_main_image_id:
                    image_dict.update({'id': int(bc_product_main_image_id)})
                if image_dict:
                    images.append(image_dict)
                for product_image_id in bc_listing_id.bigcommerce_product_listing_image_ids:
                    bc_product_image_id = bc_listing_id.bc_product_image_id
                    media_standard_image_url = web_base_url + '/web/image/bigcommerce.product.image/{}/bigcommerce_product_image/'.format(
                        product_image_id.id)
                    image_dict = {'image_url': media_standard_image_url, 'is_thumbnail': False,
                                  'url_standard': media_standard_image_url, 'url_tiny': media_standard_image_url,
                                  'description': product_image_id.name + ":" + str(product_image_id.id)}
                    if bc_product_image_id:
                        image_dict.update({'id': int(bc_product_image_id)})
                    images.append(image_dict)
                if not bc_product_id:
                    raise UserError("Product Not Sync : {}".format(product.name))
                api_operation = "/v3/catalog/products/{}".format(bc_product_id)
                product_data = self.with_context(do_not_add_variant=True).request_export_update_product_data(product, bigcommerce_store_id,
                                                                       bigcommerce_store_id.warehouse_id)
                product_data.update({'images': images})
                _logger.info("Product Data : {}".format(product_data))
                response_data = bigcommerce_store_id.update_request_from_odoo_to_bigcommerce(product_data,
                                                                                             api_operation)
                if response_data.status_code in [200, 201]:
                    # _logger.info("Get Successfull Response {0}".format(count))
                    response = response_data.json()
                    product_data.update({'id': bc_product_id})
                    listing_id = self.env['bc.store.listing'].with_context(update_bc_listing=bc_listing_id).create_or_update_bc_store_listing(product_data,
                                                                                                product,
                                                                                                bigcommerce_store_id)
                    self.update_product_variant_data_odoo_to_bc(product, bc_listing_id, bigcommerce_store_id, operation_id)
                    process_message = "Product Update Successfully : {0}".format(product.name)
                    self.sudo().create_bigcommerce_operation_detail('product', 'update', product_data, response,
                                                                    operation_id, bigcommerce_store_id.warehouse_id,
                                                                    False, process_message)
                    operation_id.bigcommerce_message = process_message
                    self._cr.commit()
                else:
                    _logger.info("Getting an Error Product >>>>> {0} >>>>> Response: {1}".format(product.name,
                                                                                                 response_data.json()))
                    process_message = "Product Not Updated Successfully : {0}".format(product.name)
                    self.sudo().create_bigcommerce_operation_detail('product', 'update', product_data,
                                                                    response_data.json(),
                                                                    operation_id, bigcommerce_store_id.warehouse_id,
                                                                    True, process_message)
                if count == 6:
                    count = 1
                    time.sleep(7)
        except Exception as e:
            process_message = "Getting an Error In Import Product Responase:{0}".format(e)
            _logger.info("Getting an Error In Import Product Responase:{0}".format(e))
            self.sudo().create_bigcommerce_operation_detail('product', 'update', False, False, operation_id,
                                                            bigcommerce_store_id.warehouse_id, False,
                                                            process_message)

    def request_update_product_inventory_data(self, product_id, warehouse_id):
        data = {
            "inventory_tracking": 'product',
            "inventory_level": int(product_id.with_context(warehouse=warehouse_id.id).qty_available) - int(
                product_id.with_context(warehouse=warehouse_id.id).outgoing_qty),
        }
        return data

    def update_product_inventory_cron(self, product_tmpl_ids=False, bigcommerce_store_ids=False, using_cron=False):
        if using_cron and bigcommerce_store_ids and product_tmpl_ids:
            bigcommerce_store_ids = self.env['bigcommerce.store.configuration'].browse(bigcommerce_store_ids)
            product_tmpl_ids = self.env['product.template'].browse(product_tmpl_ids)
        if not bigcommerce_store_ids:
            bigcommerce_store_ids = self.env['bigcommerce.store.configuration'].search([])
        for bigcommerce_store_id in bigcommerce_store_ids:
            operation_id = self.sudo().create_bigcommerce_operation('product', 'update', bigcommerce_store_id,
                                                                    'Processing...', bigcommerce_store_id.warehouse_id)
            try:
                product_data = []
                count = 1
                from_datetime = datetime.now() - relativedelta(minutes=15)
                if not product_tmpl_ids:
                    move_ids = self.env['stock.move'].search(
                        [('company_id', '=', bigcommerce_store_id.warehouse_id.company_id.id),
                         ('state', 'in', ['done', 'cancel']),
                         ('write_date', '>=', str(datetime.strftime(from_datetime, '%Y-%m-%d %H:%M:%S')))])
                    product_ids = move_ids.mapped('product_id').filtered(
                        lambda pp: pp.bigcommerce_product_id != False and pp.inventory_tracking != 'none')
                    quant_product = self.env['stock.quant'].search(
                        [('write_date', '>', fields.Datetime.now() - timedelta(minutes=30))]).mapped('product_id')
                    quant_product = quant_product.filtered(
                        lambda pp: pp.bigcommerce_product_id != False and pp.inventory_tracking != 'none')
                    prd_tmpl_ids = product_ids.mapped('product_tmpl_id')
                    quant_prd_tmpl_ids = quant_product.mapped('product_tmpl_id')
                    total_product_ids = list(set((prd_tmpl_ids.ids or []) + list(set(quant_prd_tmpl_ids.ids or []))))
                    product_tmpl_ids = self.env['product.template'].browse(total_product_ids)
                # if not product_ids:
                #     product_ids = self.search([('bigcommerce_product_id', '!=', False)], order='id')
                for product in product_tmpl_ids:
                    if product.inventory_tracking == 'product':
                        _logger.info("Inventory Tracking BY Product")
                        api_operation = "/v3/catalog/products/{}".format(product.bigcommerce_product_id)
                        count += 1
                        product_data = self.request_update_product_inventory_data(product,
                                                                                  bigcommerce_store_id.warehouse_id)
                        response_data = bigcommerce_store_id.update_request_from_odoo_to_bigcommerce(product_data,
                                                                                                     api_operation)
                        if response_data.status_code in [200, 201]:
                            response = response_data.json()
                            _logger.info("Get Successfull Response {0} : {1}".format(count, response))
                            process_message = "Product Update Successfully : {0}".format(product.name)
                            self.sudo().create_bigcommerce_operation_detail('product', 'update', product_data, response,
                                                                            operation_id,
                                                                            bigcommerce_store_id.warehouse_id,
                                                                            False, process_message)
                            self._cr.commit()
                        else:
                            _logger.info("Getting an Error Product >>>>> {0} >>>>> Response: {1}".format(product.name,
                                                                                                         response_data))
                        if count == 10:
                            count = 1
                            time.sleep(4)
                    elif product.inventory_tracking == 'variant':
                        _logger.info("Inventory Tracking BY Product Variants : {}".format(product.product_variant_ids))
                        for product_variant in product.product_variant_ids:
                            api_operation = "/v3/catalog/products/{0}/variants/{1}".format(
                                product.bigcommerce_product_id, product_variant.bigcommerce_product_variant_id)
                            product_data = {
                                # "inventory_tracking": 'variant',
                                "inventory_level": int(product_variant.with_context(
                                    warehouse=bigcommerce_store_id.warehouse_id.id).qty_available) - int(
                                    product_variant.with_context(
                                        warehouse=bigcommerce_store_id.warehouse_id.id).outgoing_qty),
                            }

                            count += 1
                            response_data = bigcommerce_store_id.update_request_from_odoo_to_bigcommerce(product_data,
                                                                                                         api_operation)
                            if response_data.status_code in [200, 201]:
                                response = response_data.json()
                                _logger.info("Get Successfull Response {0} : {1}".format(count, response))
                                process_message = "Product Update Successfully : {0}".format(product.name)
                                self.sudo().create_bigcommerce_operation_detail('product', 'update', product_data,
                                                                                response,
                                                                                operation_id,
                                                                                bigcommerce_store_id.warehouse_id,
                                                                                False, process_message)
                                self._cr.commit()
                            else:
                                _logger.info(
                                    "Getting an Error Product >>>>> {0} >>>>> Response: {1}".format(product.name,
                                                                                                    response_data))
                            if count == 10:
                                count = 1
                                time.sleep(4)
            except Exception as e:
                process_message = "Getting an Error In Update Product Inventory Responase:{0}".format(e)
                _logger.info("Getting an Error In Update Product Inventory Responase:{0}".format(e))
                self.sudo().create_bigcommerce_operation_detail('product', 'update', False, False, operation_id,
                                                                bigcommerce_store_id.warehouse_id, False,
                                                                process_message)
