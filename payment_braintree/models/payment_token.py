# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
import logging
import pprint

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    braintree_payment_method = fields.Char(string="Braintree Payment Method ID", readonly=True)
    
    
class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    braintree_cust_id = fields.Char("Braintree Customer ID")


