
import logging

from odoo import api, fields, models
_logger = logging.getLogger("BigCommerce")


class ProductTemplateExtend(models.Model):
    _inherit = "product.template"

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
        templates = super(ProductTemplateExtend, self).create(vals_list)
        # This is needed to set given values to first variant
        # after creation
        for template, vals in zip(templates, vals_list):
            related_vals = {}
            if vals.get('isbn'):
                related_vals['isbn'] = vals['isbn']
            if related_vals:
                template.write(related_vals)
        return templates
