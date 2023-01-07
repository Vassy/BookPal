
import logging
from odoo import fields, models
_logger = logging.getLogger("BigCommerce")


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    priceing_rule_id = fields.Char(string='Priceing Rule')


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    is_bigcommerce_pricelist = fields.Boolean(
        string='Is Bigcommerce Pricelist?')
    bc_store_id = fields.Many2one(
        'bigcommerce.store.configuration', string='Bigcommerce Store')
