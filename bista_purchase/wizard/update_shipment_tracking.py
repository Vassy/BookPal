from odoo import fields, models, api, _, Command

# class UpdateShipping(models.TransientModel):
#     _name = 'update.shipping'
#
# class UpdatePOLine(models.TransientModel):
#     _name = 'update.po.line'

class UpdateShipmentTracking(models.TransientModel):
    _name = 'update.shipment.tracking'
    _description = 'Update Shipment Tracking'

    order_id = fields.Many2one('purchase.order')
    tracking_lines = fields.One2many('update.shipment.tracking.line', 'update_shipping_id', string="Tracking Lines")
    # po_lines = fields.Many2many('purchase.order.line',string='Purchase Line')
    # tracking_ref = fields.Char('Tracking Ref.')
    # shipment_date = fields.Date(string="Shipment Date")
    # shipment_name = fields.Char('Shipment Name')
    status = fields.Selection([('draft', 'Draft'),
                               ('ready_for_preview', 'Ready For Preview '),
                               # ('ordered', 'Ordered '),
                               ('pending', 'Pending/In Transint'),
                               ('received', 'Received'),
                               ('stocked', 'Stocked'),
                               ('completed', 'Completed'),
                               ('return_created', 'Return created'),
                               ('rush_ordered', 'Rush Ordered'),
                               ('on_hold', 'On Hold'),
                               ('canceled', 'Canceled'),
                               ('invoiced', 'Invoiced'),
                               ('partially_received', 'Partially Received')], force_save="1")

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get('active_ids'):
            active_ids = self.env.context.get('active_ids')
            if active_ids:
                po_ids = self.env['purchase.order'].browse(active_ids)
                po_line_vals = []
                for line in po_ids.order_line:
                    po_line_vals.append((0,0, {'po_line':line.id}))
                defaults['tracking_lines'] = po_line_vals
                defaults['order_id'] = po_ids[0].id
        return defaults

    def update(self):
        po_lines = self.tracking_lines.filtered(lambda x:x.checkbox)
        po_lines.po_line.write({
            'status': self.status
        })
        # tracking_id = self.env['purchase.tracking'].create({
        #         'tracking_ref': self.tracking_ref,
        #         'shipment_date': self.shipment_date,
        #         'shipment_name': self.shipment_name,
        #         'order_id': self.order_id.id,
        #     })
        # for tracking_line in po_lines:
        #     self.env['purchase.tracking.line'].create({
        #         'tracking_id': tracking_id.id,
        #         'po_line_id': tracking_line.po_line.id,
        #         'ship_qty': tracking_line.ship_qty,
        #     })

    #     for line in self.po_lines:
    #         for purchase in line.order_id.order_line:
    #             if purchase.id == line.id:
    #                 purchase.status = self.status


class UpdateShipmentTrackingLine(models.TransientModel):
    _name = 'update.shipment.tracking.line'
    _description = 'Update Shipment Tracking Line'

    checkbox = fields.Boolean(string="CheckBox")
    update_shipping_id = fields.Many2one('update.shipment.tracking', "Update Shipping")
    po_line = fields.Many2one('purchase.order.line', 'PO Line')
    status = fields.Selection(related="po_line.status")
    # ship_qty = fields.Float(string="Ship Quantity")
