# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_never_report = fields.Boolean(string="Never Report", default=False)


class ProductProduct(models.Model):
    _inherit = "product.product"

    def get_product_multiline_description_sale(self):
        """ Compute a multiline description of this product, in the context of sales
                (do not use for purchases or other display reasons that don't intend to use "description_sale").
            It will often be used as the default description of a sale order line referencing this product.
        """
        name = super(ProductProduct, self).get_product_multiline_description_sale()
        if self.detailed_type == 'consu':
            variant_name = ", ".join([variant[:variant.find('(')] for variant in self.product_template_attribute_value_ids.mapped('name')])
            name = variant_name and "%s (%s)" % (self.name, variant_name) or self.name
        return name