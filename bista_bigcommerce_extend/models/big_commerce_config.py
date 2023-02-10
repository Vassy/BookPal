# -*- coding: utf-8 -*-

import logging

from odoo import fields, models

_logger = logging.getLogger("BigCommerce")


class BigCommerceStoreConfiguration(models.Model):
    _inherit = "bigcommerce.store.configuration"

    bc_export_shipment = fields.Boolean(
        string="Bigcommerce Export Shipment", default=False
    )
