
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_format = fields.Char('Format')
    publisher_id = fields.Many2one('res.partner', 'Publisher')
    author_id = fields.Many2one('res.partner', 'Author')
    origin = fields.Char('Origin')


class ProductProduct(models.Model):
    _inherit = "product.product"

    isbn = fields.Char('ISBN')
