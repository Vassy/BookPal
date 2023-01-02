
from odoo import api, fields, models
from odoo.addons.product.models.product import ProductProduct


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_format = fields.Char('Format')
    publisher_id = fields.Many2one('res.partner', 'Publisher')
    author_ids = fields.Many2many(
        'res.partner', string='Author(s)')
    origin = fields.Char('Origin')
    isbn = fields.Char(
        'ISBN', compute='_compute_isbn',
        inverse='_set_isbn', store=True)
    bigcommerce_description = fields.Html('BigCommerce Product Description')

    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_isbn(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.isbn = template.product_variant_ids.isbn
        for template in (self - unique_variants):
            template.isbn = False

    def _set_isbn(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.isbn = template.isbn

    @api.model_create_multi
    def create(self, vals_list):
        """Set isbn in first variant."""
        templates = super(ProductTemplate, self).create(vals_list)
        # This is needed to set given values to first variant
        # after creation
        for template, vals in zip(templates, vals_list):
            related_vals = {}
            if vals.get('isbn'):
                related_vals['isbn'] = vals['isbn']
            if related_vals:
                template.write(related_vals)
        return templates

    def create_product_template(self, record, store_id):
        """ Overwrite the method to update the description of product in new 
            Big commerce product description field
        """
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
            "bigcommerce_description": record.get('description'),
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
                                        "bigcommerce_description": record.get('description'),
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


class ProductExtend(models.Model):
    _inherit = "product.product"

    isbn = fields.Char('ISBN')

    # @api.depends('list_price', 'price_extra', 'bc_sale_price')
    # @api.depends_context('uom')
    # def _compute_product_lst_price(self):
    #     to_uom = None
    #     if 'uom' in self._context:
    #         to_uom = self.env['uom.uom'].browse(self._context['uom'])

    #     for product in self:
    #         if to_uom:
    #             list_price = product.uom_id._compute_price(
    #                 product.list_price, to_uom)
    #         else:
    #             list_price = product.list_price
    #         list_price = list_price + product.price_extra
    #         if product.bigcommerce_product_variant_id:
    #             product.lst_price = product.bc_sale_price
    #         else:
    #             product.lst_price = list_price

    # ProductProduct._compute_product_lst_price = \
    #     _compute_product_lst_price


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_publisher = fields.Boolean('Is Publisher?')
    is_author = fields.Boolean('Is Author?')
