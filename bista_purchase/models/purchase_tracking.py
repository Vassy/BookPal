# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class PurchaseTracking(models.Model):
    _name = 'purchase.tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Purchase Tracking'
    _order = 'tracking_ref'

    order_id = fields.Many2one('purchase.order', string="Order")

    partner_id = fields.Many2one(related='order_id.partner_id')
    date_approve = fields.Datetime(related='order_id.date_approve')
    date_order = fields.Datetime(related='order_id.date_order')
    picking_type_id = fields.Many2one(related="order_id.picking_type_id")
    carrier_id = fields.Many2one('delivery.carrier', "Carrier")
    tracking_ref = fields.Char('Tracking Ref.', tracking=True)
    shipment_date = fields.Date(string="Shipment Date", tracking=True)
    pro_number = fields.Char('Pro Number', tracking=True)
    tracking_line_ids = fields.One2many('purchase.tracking.line', 'tracking_id', string="Tracking Lines")
    status = fields.Selection([('draft', 'Draft'),
                               ('pending', 'Pending/In Transint'),
                               ('received', 'Received'),
                               ('on_hold', 'On Hold')], default='draft', tracking=True)
    tracking_ref_ids = fields.One2many('purchase.tracking.ref', 'purchase_tracking_id', string="Tracking Refs")

    def save(self):
        return self

    @api.onchange('status')
    def onchange_status(self):
        po_line_vals = []
        for line in self.order_id.order_line:
            po_line_vals.append((0, 0, {'po_line_id': line.id, 'product_id':line.product_id}))
        self.tracking_line_ids = po_line_vals

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get('active_ids'):
            active_ids = self.env.context.get('active_ids')
            if active_ids:
                po_ids = self.env['purchase.order'].browse(active_ids)
                po_line_vals = []
                for line in po_ids.order_line:
                    po_line_vals.append((0, 0, {'po_line_id': line.id, 'product_id': line.product_id}))
                defaults['tracking_line_ids'] = po_line_vals
                defaults['order_id'] = po_ids[0].id
        return defaults


class PurchaseTrackingRef(models.Model):
    _name = 'purchase.tracking.ref'

    purchase_tracking_id = fields.Many2one('purchase.tracking', '')
    name = fields.Char(string='Name')
    link = fields.Char(string="Link", compute="compute_link_from_ref")

    @api.depends('name')
    def compute_link_from_ref(self):
        for each in self:
            each.link = each.name

class PurchaseTrackingLine(models.Model):
    _name = 'purchase.tracking.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Purchase Tracking Line'

    checkbox = fields.Boolean(string="Checkbox", compute="compute_checkbox")
    tracking_id = fields.Many2one('purchase.tracking', string="Tracking")
    po_line_id = fields.Many2one('purchase.order.line', 'PO Line')
    order_qty = fields.Float(related='po_line_id.product_qty', string="Ordered Quantity")
    product_id = fields.Many2one('product.product', 'Product')
    ship_qty = fields.Float(string="Shipped Quantity")

    def compute_checkbox(self):
        for each in self:
            each.checkbox = False

    @api.onchange('checkbox')
    def _onchange_checkbox(self):
        self.ship_qty = self.order_qty
