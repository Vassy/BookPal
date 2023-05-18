# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_never_report = fields.Boolean(string="Never Report", default=False)
    publication_date = fields.Date(string="Publication Date", tracking=True)

    def write(self, vals):
        if self._context.get("from_bc_to_odoo") and vals.get("list_price"):
            self.seller_ids.write({"price": vals.get("list_price")})
        return super().write(vals)

    def name_get(self):
        if self._context.get("display_default_code", True):
            return super().name_get()
        self.browse(self.ids).read(["name"])
        return [(template.id, "%s" % (template.name)) for template in self]


class ProductProduct(models.Model):
    _inherit = "product.product"

    def price_compute(self, price_type, uom=False, currency=False, company=None):
        """Overiden method to change price in product configurator."""
        # TDE FIXME: delegate to template or not ? fields are reencoded
        # here ...
        # compatibility about context keys used a bit everywhere in the code
        if not uom and self._context.get("uom"):
            uom = self.env["uom.uom"].browse(self._context["uom"])
        if not currency and self._context.get("currency"):
            currency = self.env["res.currency"].browse(self._context["currency"])

        products = self
        if price_type == "standard_price":
            # standard_price field can only be seen by users in base.group_user
            # Thus, in order to compute the sale price from the cost for
            # users not in this group
            # We fetch the standard price as the superuser
            products = self.with_company(company or self.env.company).sudo()

        prices = dict.fromkeys(self.ids, 0.0)
        for product in products:
            prices[product.id] = product[price_type] or 0.0
            if price_type == "list_price":
                prices[product.id] += product.price_extra
                # if variant has no extra price then use sale price of variant
                if not product.price_extra:
                    prices[product.id] = product.lst_price
                # we need to add the price from the attributes that do
                # not generate variants
                # (see field product.attribute create_variant)
                if self._context.get("no_variant_attributes_price_extra"):
                    # we have a list of price_extra that comes from
                    # the attribute values, we need to sum all that
                    prices[product.id] += sum(
                        self._context.get("no_variant_attributes_price_extra")
                    )

            if uom:
                prices[product.id] = product.uom_id._compute_price(
                    prices[product.id], uom
                )

            # Convert from current user company currency to asked one
            # This is right cause a field cannot be in more than one currency
            if currency:
                prices[product.id] = product.currency_id._convert(
                    prices[product.id],
                    currency,
                    product.company_id,
                    fields.Date.today(),
                )
        return prices
