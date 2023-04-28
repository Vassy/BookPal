# -*- coding: utf-8 -*-

from lxml import etree

from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    has_tracking_made_by_automation = fields.Boolean('Has Tracking made by Automation', default=False, copy=False)
