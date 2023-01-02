# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from copy import deepcopy

from odoo import models, api, _, fields


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    def name_get(self):
        result = []
        for bbd_type in self:
            result.append((bbd_type.id, bbd_type.display_name , bbd_type.block))
        return result