# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
