# -*- coding: utf-8 -*-

from odoo.osv import expression
from odoo import models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _search(
        self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None
    ):
        """Select specific contacts based on different context and user access"""
        if self._context.get("cc_parent_ids"):
            internal_users = self.env.ref("base.group_user").users
            custom_args = [
                "|",
                ("parent_id", "in", self._context["cc_parent_ids"][0][-1]),
                ("id", "in", internal_users.mapped("partner_id").ids),
            ]
            args = expression.AND([args, custom_args])
        return super()._search(args, offset, limit, order, count, access_rights_uid)

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        """Updated search more domain when open vendors in shipping line."""
        if self._context.get("cc_parent_ids"):
            internal_users = self.env.ref("base.group_user").users
            custom_domain = [
                "|",
                ("parent_id", "in", self._context["cc_parent_ids"][0][-1]),
                ("id", "in", internal_users.mapped("partner_id").ids),
            ]
            domain = expression.AND([domain, custom_domain])
        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)
