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
        result = super(ResPartnerInherit, self).name_get()
        if self.env.context.get('custom_code'):
            custom_result = []
            for i in result:
                partner_id = self.browse(i[0])
                lst = list(i)
                if partner_id.parent_id:
                    lst.append(partner_id.parent_id.block)
                else:
                    lst.append(partner_id.block)
                i = tuple(lst)
                custom_result.append(i)
            return custom_result
        return result
