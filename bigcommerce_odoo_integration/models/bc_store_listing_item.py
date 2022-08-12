from odoo import fields,models,api
from odoo.exceptions import ValidationError
import requests
import json
import base64
import logging
from datetime import datetime
_logger = logging.getLogger("Bigcommerce")

class BigcommerceStoreListingItem(models.Model):
    _name = "bc.store.listing.item"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Bigcommerce Store Listing Item'

    # def _compute_sales_price_with_currency(self):
    #     for record in self:
    #         instance_id = record.mk_instance_id or record.mk_listing_id.mk_instance_id
    #         pricelist_item_id = self.env['product.pricelist.item'].search([('pricelist_id', '=', instance_id.pricelist_id.id), ('product_id', '=', record.product_id.id)], order='id', limit=1)
    #         record.sale_price = pricelist_item_id.fixed_price or False
    #         record.currency_id = pricelist_item_id.currency_id.id or False

    name = fields.Char('Name', required=True)
    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade')
    default_code = fields.Char('Internal Reference')
    sequence = fields.Integer(help="Determine the display order", default=10)
    bc_product_id = fields.Char("Marketplace Identification", copy=False)
    bc_listing_id = fields.Many2one('bc.store.listing', "Listing", ondelete="cascade")
    bigcommerce_store_id = fields.Many2one('bigcommerce.store.configuration', "Instance", ondelete='cascade')

    item_create_date = fields.Datetime("Creation Date", readonly=True, index=True)
    item_update_date = fields.Datetime("Updated On", readonly=True)
    is_listed = fields.Boolean("Listed?", copy=False)
    #image_ids = fields.Many2many('mk.listing.image', 'mk_listing_image_listing_rel', 'listing_item_id', 'mk_listing_image_id', string="Images")
    sale_price = fields.Monetary(string='Sale Price', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, string='Currency')
    pro_atr_values_name = fields.Char(string="Attribute Values")

    def create_or_update_bc_store_listing_item(self,product_data,variant_data,product_tmpl_id,bigcommerce_store_id,listing_id,product_variant_id):
        vals = {
            "name": product_data.get('name'),
            "bc_listing_id":listing_id.id,
            "default_code": variant_data.get('sku', ''),
            "bigcommerce_store_id": bigcommerce_store_id.id,
            "bc_product_id": variant_data.get('id'),
            "product_id": product_tmpl_id.id,
            "item_create_date": datetime.now(),
            "sale_price":variant_data.get('sale_price'),
            "product_id":product_variant_id.id,
            "is_listed":True,
            "pro_atr_values_name":','.join(product_variant_id.product_template_attribute_value_ids.mapped('name'))
        }
        listing_id = self.create(vals)
        return listing_id