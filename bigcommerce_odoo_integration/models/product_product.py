from odoo import fields, models, api
from odoo.addons.product.models.product import ProductProduct

class ProductProduct(models.Model):
    _inherit = "product.product"

    bigcommerce_product_variant_id = fields.Char(string='Bigcommerce Product Variant ID')
    bc_sale_price = fields.Float(string='BC Sale Price')

@api.depends('list_price', 'price_extra', 'bc_sale_price')
@api.depends_context('uom')
def _compute_product_lst_price(self):
    to_uom = None
    if 'uom' in self._context:
        to_uom = self.env['uom.uom'].browse(self._context['uom'])

    for product in self:
        if to_uom:
            list_price = product.uom_id._compute_price(product.list_price, to_uom)
        else:
            list_price = product.list_price
        list_price = list_price + product.price_extra
        if product.bigcommerce_product_variant_id:
            product.lst_price = product.bc_sale_price
        else:
            product.lst_price = list_price


ProductProduct._compute_product_lst_price = _compute_product_lst_price