from odoo import fields,models,api
import logging
_logger = logging.getLogger("Bigcommerce")

class BigcommerceOrderStatus(models.Model):
    _name = "bigcommerce.order.status"
    _description = 'Bigcommerce Order Status'

    key = fields.Char(string='Key')
    name = fields.Char(string='Status Name')