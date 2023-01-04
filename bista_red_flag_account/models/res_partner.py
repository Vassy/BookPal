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
        if self.env.context.get('custom_code'):
            for partner in self:
                if partner.is_multi_ship:
                    result.append((partner.id, partner.name, partner.block))
                else:
                    result.append(
                        (partner.id, partner.display_name, partner.block))
        else:
            result = super(ResPartnerInherit, self).name_get()
        return result
