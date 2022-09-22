# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    used_for = fields.Selection([('sale',"Sale"),('purchase',"Purchase")], default='sale')

    def _get_partner_pricelist_multi_search_domain_hook(self, company_id):
        res = super(ProductPricelist, self)._get_partner_pricelist_multi_search_domain_hook(company_id)
        res.append(('used_for', '=', 'sale'))
        return res
