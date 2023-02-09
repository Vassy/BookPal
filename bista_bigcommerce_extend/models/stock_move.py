# -*- coding: utf-8 -*-
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sequence_code = fields.Char(
        related="picking_type_id.sequence_code", string="Sequence Code")


class StockMove(models.Model):
    _inherit = "stock.move"

    publisher_id = fields.Char(
        related="product_tmpl_id.publisher_id", string="Publisher")


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    publisher_id = fields.Char(
        related="product_id.publisher_id", string="Publisher")
    demand_qty = fields.Float(related="move_id.product_uom_qty", store=True, readonly=True)
