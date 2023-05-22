# -*- coding: utf-8 -*-

from odoo import fields, models


class CustomizationType(models.Model):

    _name = "customization.type"
    _description = "Customization Type"

    name = fields.Char("Name")
