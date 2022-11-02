# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class PurchaseTracking(models.Model):
    _name = 'purchase.tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Purchase Tracking'
    _order = 'tracking_ref'

    order_id = fields.Many2one('purchase.order', string="Order")
    tracking_ref = fields.Char('Tracking Ref.', tracking=True)
    shipment_date = fields.Date(string="Shipment Date", tracking=True)
    shipment_name = fields.Char('Shipment Name', tracking=True)
    tracking_line_ids = fields.One2many('purchase.tracking.line', 'tracking_id', string="Tracking Lines")


class PurchaseTrackingLine(models.Model):
    _name = 'purchase.tracking.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Purchase Tracking Line'

    tracking_id = fields.Many2one('purchase.tracking', string="Tracking")
    po_line_id = fields.Many2one('purchase.order.line', 'PO Line')
    ship_qty = fields.Float(string="Ship Quantity")
