from odoo import fields,models,api
from odoo.exceptions import ValidationError
import requests
from datetime import timedelta
import requests
import json
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from datetime import datetime
import json
import base64
import logging
_logger = logging.getLogger("Bigcommerce")

class BigcommerceStoreListing(models.Model):
    _name = "bc.store.listing"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Bigcommerce Store Listing'

    def _listing_item_count(self):
        for listing in self:
            listing.item_count = len(listing.listing_item_ids)


    name = fields.Char(string='Listing Name')
    default_code = fields.Char(string='Internal Ref')
    bigcommerce_store_id = fields.Many2one('bigcommerce.store.configuration',string='BC Store',ondelete='cascade')
    bc_product_id = fields.Char(string='BC PRoduct ID',copy=False)
    product_tmpl_id = fields.Many2one('product.template')
    listing_item_ids = fields.One2many("bc.store.listing.item", "bc_listing_id", "Listing Items")
    item_count = fields.Integer("Items", compute='_listing_item_count')
    listing_create_date = fields.Datetime("Creation Date", readonly=True, index=True)
    listing_update_date = fields.Datetime("Updated On", readonly=True)
    description = fields.Html('Description', sanitize_attributes=False)
    is_listed = fields.Boolean("Listed?", copy=False)
    is_published = fields.Boolean("Published", copy=False)
    product_category_id = fields.Many2one('product.category',string='Product Category')
    ecommerce_category_ids = fields.Many2many('product.public.category',string='Ecommerce Category')
    #image_ids = fields.One2many('mk.listing.image', 'mk_listing_id', 'Images')
    bigcommerce_product_listing_image_ids = fields.One2many('bigcommerce.product.image', 'bigcommerce_listing_id',
                                                    string="Bigcommerce Product Image Ids")
    number_of_variants_in_mk = fields.Integer("Number of Variants in Marketplace.")
    image_1920 = fields.Image("Image", copy=False)
    bc_product_image_id = fields.Char(string='BC Product Image', copy=False)

    def create_or_update_bc_store_listing(self,product_data,product_tmpl_id,bigcommerce_store_id):
        category_id = self.env.ref('product.product_category_all')
        if not category_id:
            message = "Category not found!"
            _logger.info("Category not found: {}".format(category_id))
            return False, message
        public_category_ids = self.env['product.public.category'].sudo().search(
            [('bigcommerce_product_category_id', 'in', product_data.get('categories'))])
        vals = {
            "name":product_data.get('name'),
            "default_code":product_data.get('sku',''),
            "bc_product_id":product_data.get('id'),
            "description":product_data.get('description'),
            "product_category_id":category_id.id,
            "ecommerce_category_ids":[(6,0,public_category_ids.ids or [])]
        }

        update_bc_listing = self._context.get('update_bc_listing', False)
        if update_bc_listing:
            update_bc_listing.write(vals)
            return update_bc_listing

        vals.update({
            "bigcommerce_store_id": bigcommerce_store_id.id,
            "product_tmpl_id": product_tmpl_id.id,
            "listing_create_date": datetime.now(),
            "is_listed": True,
            "is_published": True
        })
        listing_id = self.create(vals)
        return listing_id

    def get_odoo_product_variant_and_listing_item(self, bc_store_id, variant_id, variant_barcode, variant_sku):
        odoo_product_obj, bc_store_listing_item_obj, odoo_product_id = self.env['product.product'], self.env['bc.store.listing.item'], False
        listing_item_id = bc_store_listing_item_obj.search([('bc_product_id', '=', variant_id), ('bigcommerce_store_id', '=', bc_store_id.id)], limit=1)
        if not listing_item_id and variant_sku:
            odoo_product_id = odoo_product_obj.search([('default_code', '=', variant_sku)], limit=1)
        if not odoo_product_id and not listing_item_id and variant_barcode:
            odoo_product_id = odoo_product_obj.search([('barcode', '=', variant_barcode)], limit=1)
        if variant_sku and not listing_item_id:
            listing_item_id = bc_store_listing_item_obj.search([('default_code', '=', variant_sku), ('bc_product_id', '=', variant_id),
                                                          ('bigcommerce_store_id', '=', bc_store_id.id)], limit=1)
        return odoo_product_id or listing_item_id.product_id, listing_item_id

    def get_existing_mk_listing_and_odoo_product(self, bc_variant_list, bc_store_id):
        existing_mk_product = {}
        existing_odoo_product = {}
        odoo_product_template = self.env['product.template']
        for variant_dict in bc_variant_list:
            odoo_product_id, listing_item_id = self.get_odoo_product_variant_and_listing_item(bc_store_id, variant_dict.get("id", ""), variant_dict.get("barcode", ""),
                                                                                              variant_dict.get("sku", ""))
            if odoo_product_id:
                odoo_product_template |= odoo_product_id.product_tmpl_id
                existing_odoo_product.update({variant_dict.get("id"): odoo_product_id})
            elif listing_item_id and not odoo_product_id:
                existing_odoo_product.update({variant_dict.get("id"): listing_item_id.product_id})
            listing_item_id and existing_mk_product.update({variant_dict.get("id"): listing_item_id})
        return existing_mk_product, existing_odoo_product, odoo_product_template
