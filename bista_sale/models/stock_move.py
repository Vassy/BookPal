# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sequence_code = fields.Char(related="picking_type_id.sequence_code", string="Sequence Code")


class StockMove(models.Model):
    _inherit = "stock.move"

    publisher_id = fields.Many2one(related="product_tmpl_id.publisher_id", string="Publisher")


    class StockMove(models.Model):
        _inherit = "stock.move.line"

        publisher_id = fields.Many2one(related="product_id.publisher_id", string="Publisher")
