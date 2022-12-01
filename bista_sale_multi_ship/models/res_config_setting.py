# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    group_hide_contact = fields.Boolean(
        "Show Multi Ship Contact",
        implied_group='bista_sale_multi_ship.show_multi_ship_contact')
