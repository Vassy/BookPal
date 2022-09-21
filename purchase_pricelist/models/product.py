# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Product(models.Model):
    _inherit = "product.product"

    vendor_price = fields.Float('Price', compute='_compute_vendor_product_price', digits='Product Price')

    @api.depends_context('pricelist', 'partner', 'quantity', 'uom', 'date', 'no_variant_attributes_price_extra')
    def _compute_vendor_product_price(self):
        prices = {}
        pricelist_id_or_name = self._context.get('pricelist')
        if pricelist_id_or_name:
            pricelist = None
            partner = self.env.context.get('partner', False)
            quantity = self.env.context.get('quantity', 1.0)

            # Support context pricelists specified as list, display_name or ID for compatibility
            if isinstance(pricelist_id_or_name, list):
                pricelist_id_or_name = pricelist_id_or_name[0]
            if isinstance(pricelist_id_or_name, str):
                pricelist_name_search = self.env['product.pricelist'].name_search(pricelist_id_or_name, operator='=', limit=1)
                if pricelist_name_search:
                    pricelist = self.env['product.pricelist'].browse([pricelist_name_search[0][0]])
            elif isinstance(pricelist_id_or_name, int):
                pricelist = self.env['product.pricelist'].browse(pricelist_id_or_name)

            if pricelist:
                quantities = [quantity] * len(self)
                partners = [partner] * len(self)
                prices = pricelist.get_products_price(self, quantities, partners)

        for product in self:
            product.vendor_price = prices.get(product.id, 0.0)

    def price_compute(self, price_type, uom=False, currency=False, company=None):
        if not self._context.get('seller'):
            return super(Product, self).price_compute(price_type, uom, currency, company)

        if not uom and self._context.get('uom'):
            uom = self.env['uom.uom'].browse(self._context['uom'])
        if not currency and self._context.get('currency'):
            currency = self.env['res.currency'].browse(self._context['currency'])

        products = self
        if price_type == 'standard_price':
            products = self.with_company(company or self.env.company).sudo()

        prices = dict.fromkeys(self.ids, 0.0)
        for product in products:
            prices[product.id] = product[price_type] or 0.0

            if self._context.get('seller'):
                prices[product.id] = self._context.get('seller').price
            if uom:
                prices[product.id] = product.uom_id._compute_price(prices[product.id], uom)

            if currency:
                prices[product.id] = product.currency_id._convert(
                    prices[product.id], currency, product.company_id, fields.Date.today())

        return prices
