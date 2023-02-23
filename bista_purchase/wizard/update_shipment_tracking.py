# -*- coding: utf-8 -*-
from odoo import fields, models, api


class UpdateShipmentTracking(models.TransientModel):
    _name = "update.shipment.tracking"
    _description = "Update Shipment Tracking"

    order_id = fields.Many2one("purchase.order")
    partner_id = fields.Many2one(related="order_id.partner_id")
    date_approve = fields.Datetime(related="order_id.date_approve")
    date_order = fields.Datetime(related="order_id.date_order")
    picking_type_id = fields.Many2one(related="order_id.picking_type_id")
    tracking_lines = fields.One2many(
        "update.shipment.tracking.line", "update_shipping_id"
    )
    status_id = fields.Many2one("po.status.line", string="Status")
    checkbox = fields.Boolean("Update All PO Lines")
    next_followup_date = fields.Date("Next Followup Date")
    note = fields.Text("Notes")

    @api.onchange("checkbox")
    def _onchange_checkbox(self):
        for line in self.tracking_lines:
            line.checkbox = self.checkbox

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        context = self._context
        po_id = self.env[context.get("active_model")].browse(context.get("active_id"))
        if po_id:
            po_line_vals = []
            for line in po_id.order_line:
                po_line_vals.append((0, 0, {"po_line_id": line.id}))
            defaults.update({"tracking_lines": po_line_vals, "order_id": po_id.id})
        return defaults

    def update(self):
        self.ensure_one()
        po_lines = self.tracking_lines.filtered(lambda x: x.checkbox)
        line_data = {
            "status_id": self.status_id.id,
            "next_followup_date": self.next_followup_date,
            "note": self.note,
        }
        po_lines.po_line_id.write(line_data)


class UpdateShipmentTrackingLine(models.TransientModel):
    _name = "update.shipment.tracking.line"
    _description = "Update Shipment Tracking Line"

    checkbox = fields.Boolean(string="Checkbox")
    update_shipping_id = fields.Many2one("update.shipment.tracking", "Update Shipping")
    po_line_id = fields.Many2one("purchase.order.line", "PO Line")
    status_id = fields.Many2one(related="po_line_id.status_id")
    product_qty = fields.Float(related="po_line_id.product_qty")
