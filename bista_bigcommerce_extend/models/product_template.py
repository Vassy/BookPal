
import logging

from odoo import api, fields, models
from odoo.addons.product.models.product import ProductProduct

_logger = logging.getLogger("BigCommerce")


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
