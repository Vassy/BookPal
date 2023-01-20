from odoo import fields, models, api
from odoo.exceptions import ValidationError
import requests
import json
import base64
import logging

_logger = logging.getLogger("Bigcommerce")


class BCPaymentJournal(models.Model):
    _name = "bc.payment.journal"
    _description = 'Bigcommerce Payment Journal'

    name = fields.Char(string='Payment Method Name')
    journal_id = fields.Many2one('account.journal',string='Payment Journal',domain=[('type','in',['bank','cash'])])