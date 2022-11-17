# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class PurchaseTracking(models.Model):
    _name = 'purchase.tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Purchase Tracking'
    _order = 'name'

    order_id = fields.Many2one('purchase.order', string="Order")
    name = fields.Char(string='Number', required=True, copy=False, default=lambda self: _('New'))
    partner_id = fields.Many2one(related='order_id.partner_id')
    date_approve = fields.Datetime(related='order_id.date_approve')
    date_order = fields.Datetime(related='order_id.date_order')
    picking_type_id = fields.Many2one(related="order_id.picking_type_id")
    carrier_id = fields.Many2one('delivery.carrier', "Carrier")
    # tracking_ref = fields.Char('Tracking Ref.', tracking=True)
    shipment_date = fields.Date(string="Shipment Date", tracking=True)
    pro_number = fields.Char('PRO No.', tracking=True)
    tracking_line_ids = fields.One2many('purchase.tracking.line', 'tracking_id', string="Tracking Lines")
    status = fields.Selection([('draft', 'Draft'),
                               ('pending', 'Pending/In Transint'),
                               ('received', 'Received'),
                               ('on_hold', 'On Hold')], default='pending', tracking=True, string="Shipment Status")
    tracking_ref_ids = fields.One2many('purchase.tracking.ref', 'purchase_tracking_id', string="Tracking Refs")
    picking_ids = fields.One2many('stock.picking', 'purchase_tracking_id', "Pickings")
    is_read_only = fields.Boolean(compute="_compute_is_read_only", string="Is Read Only")

    def name_get(self):
        if not self._context.get('shipping_selection'):
            return super(PurchaseTracking, self).name_get()
        res = []
        for purchase_tracking in self:
            tracking_names = purchase_tracking.tracking_ref_ids.mapped('name')
            if tracking_names:
                name = "{} [{}]".format(purchase_tracking.name, ",".join(tracking_names))
            else:
                name = purchase_tracking.name
            res.append((purchase_tracking.id, name))
        return res

    def _compute_is_read_only(self):
        for tracking in self:
            if tracking.picking_ids.mapped('state'):
                tracking.is_read_only = tracking.picking_ids and tracking.picking_ids[0].state == 'done'
            else:
                tracking.is_read_only = False

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.tracking') or _('New')
        return super(PurchaseTracking, self).create(vals)

    def save(self):
        return self

    @api.onchange('order_id')
    def onchange_order_id(self):
        po_line_vals = []
        for line in self.order_id.order_line:
            po_line_vals.append((0, 0, {'po_line_id': line.id, 'product_id':line.product_id}))
        self.tracking_line_ids = po_line_vals

    # @api.model
    # def default_get(self, fields_list):
    #     defaults = super().default_get(fields_list)
    #     if self.env.context.get('active_ids'):
    #         active_ids = self.env.context.get('active_ids')
    #         if active_ids:
    #             po_ids = self.env['purchase.order'].browse(active_ids)
    #             po_line_vals = []
    #             for line in po_ids.order_line:
    #                 po_line_vals.append((0, 0, {'po_line_id': line.id, 'product_id': line.product_id}))
    #             defaults['tracking_line_ids'] = po_line_vals
    #             defaults['order_id'] = po_ids[0].id
    #     return defaults


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
    ordered_qty = fields.Float(compute="_compute_quantities", string="Ordered Quantity", store=True)
    received_qty = fields.Float(compute="_compute_quantities", string="Received Quantity", store=True)
    pending_shipment_qty = fields.Float(compute="_compute_quantities", string="Pending Shipment", store=False)
    product_id = fields.Many2one('product.product', 'Product')
    ship_qty = fields.Float(string="Shipped Quantity")

    @api.depends('po_line_id', 'ship_qty')
    def _compute_quantities(self):
        for tracking_line in self:
            tracking_line.ordered_qty = tracking_line.po_line_id.product_qty
            tracking_line.received_qty = tracking_line.po_line_id.qty_received
            purchase_tracking_line_ids = tracking_line.po_line_id.purchase_tracking_line_ids.filtered(lambda x:x.tracking_id.status!='cancel')
            tracking_line.pending_shipment_qty = tracking_line.ordered_qty - sum(purchase_tracking_line_ids.mapped('ship_qty'))

    def compute_checkbox(self):
        for each in self:
            each.checkbox = False

    @api.onchange('checkbox')
    def _onchange_checkbox(self):
        self.ship_qty = self.remaining_qty
