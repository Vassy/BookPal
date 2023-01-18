# -*- coding: utf-8 -*-

from odoo import api, models
from lxml import etree


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def _fields_view_get(
            self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super()._fields_view_get(view_id, view_type, toolbar, submenu)
        if view_type != "tree":
            return result
        doc = etree.XML(result["arch"])
        for node in doc.xpath("//field[@name='partner_id']"):
            if self._context.get("is_incoming", False) or self._context.get("is_dropship", False):
                node.set('string', "Receive from")
            if self._context.get("is_outgoing", False):
                node.set('string', "Ship To")
        result["arch"] = etree.tostring(doc)
        return result


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    def _get_action(self, action_xmlid):
        action = super()._get_action(action_xmlid)
        action.get('context',False).update({
            'is_incoming' : True if self.sequence_code == 'IN' else False,
            'is_outgoing': True if self.sequence_code == 'OUT' else False,
            'is_dropship': True if self.sequence_code == 'DS' else False,
        })
        return action