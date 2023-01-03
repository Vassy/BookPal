# -*- coding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, api, _, fields


class ResPartnerInherit(models.Model):
    '''Inherit res partner for customisation'''
    _inherit = "res.partner"

    def name_get(self):
        '''Pass custom parameter for red flag account'''
        result = []
        for bbd_type in self:
            result.append((bbd_type.id, bbd_type.display_name, bbd_type.block))
        return result
