# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class PurchaseTracking(models.Model):
    _name = "purchase.tracking"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Purchase Tracking"
    _order = "name"

    order_id = fields.Many2one("purchase.order", string="Order")
    name = fields.Char(
        string="Number", required=True, copy=False, default=lambda self: _("New")
    )
    partner_id = fields.Many2one(related="order_id.partner_id")
    date_approve = fields.Datetime(related="order_id.date_approve")
    date_order = fields.Datetime(related="order_id.date_order")
    picking_type_id = fields.Many2one(related="order_id.picking_type_id")
    dest_address_id = fields.Many2one(related="order_id.dest_address_id")
    carrier_id = fields.Many2one("delivery.carrier", "Carrier")
    delivery_type = fields.Selection(related="carrier_id.delivery_type")
    shipment_date = fields.Date(string="Shipment Date", tracking=True)
    pro_number = fields.Char("PRO No.", tracking=True)
    tracking_line_ids = fields.One2many("purchase.tracking.line", "tracking_id")
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Awaiting Shipment"),
            ("received", "Received"),
            ("shipped", "Shipped"),
            ("on_hold", "On Hold"),
        ],
        default="pending",
        tracking=True,
        string="Shipment Status",
    )
    tracking_ref_ids = fields.One2many(
        "purchase.tracking.ref", "purchase_tracking_id", string="Tracking Refs"
    )
    picking_ids = fields.One2many("stock.picking", "purchase_tracking_id", "Pickings")
    is_read_only = fields.Boolean(
        compute="_compute_is_read_only", string="Is Read Only"
    )
    checkbox = fields.Boolean(string="Select All (Pending to Shipped)")
    is_automated = fields.Boolean(string="is Automated", default=False, copy=False)

    def save(self):
        return {"type": "ir.actions.act_window_close"}

    def confirm_tracking(self):
        self.ensure_one()
        if not self.dest_address_id:
            return False
        picking_data = {
            "purchase_tracking_id": self.id,
            "carrier_id": self.carrier_id.id,
            "carrier_tracking_ref": ",".join(self.tracking_ref_ids.mapped("name")),
        }
        self.order_id.picking_ids.filtered(lambda p: p.state != "done").write(
            picking_data
        )
        open_move = self.env["stock.move"]
        for line in self.tracking_line_ids.filtered(lambda l: l.ship_qty):
            move_ids = line.po_line_id.move_ids.filtered(lambda m: m.state != "done")
            open_move |= move_ids
            move_ids.write({"quantity_done": line.ship_qty})
        open_move._action_done()
        self.status = "shipped"

    @api.onchange("checkbox")
    def _onchange_checkbox(self):
        for line in self.tracking_line_ids:
            line.checkbox = self.checkbox
            line._onchange_checkbox()

    def name_get(self):
        if not self._context.get("shipping_selection"):
            return super(PurchaseTracking, self).name_get()
        res = []
        for purchase_tracking in self:
            tracking_names = purchase_tracking.tracking_ref_ids.mapped("name")
            name = (
                "{} [{}]".format(purchase_tracking.name, ", ".join(tracking_names))
                if tracking_names
                else purchase_tracking.name
            )
            res.append((purchase_tracking.id, name))
        return res

    def _compute_is_read_only(self):
        for tracking in self:
            if tracking.picking_ids.mapped("state"):
                tracking.is_read_only = (
                    tracking.picking_ids and tracking.picking_ids[0].state == "done"
                )
            else:
                tracking.is_read_only = False

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "purchase.tracking"
            ) or _("New")
        return super(PurchaseTracking, self).create(vals)

    @api.onchange("order_id")
    def onchange_order_id(self):
        po_line_vals = []
        for line in self.order_id.order_line:
            po_line_vals.append((0, 0, {"po_line_id": line.id}))
        self.tracking_line_ids = po_line_vals

    def send_email(self):
        self.ensure_one()
        if not self.tracking_line_ids.filtered(lambda t: t.ship_qty):
            raise ValidationError("Please set shipped quantity on tracking line.")
        template_id = self.env.ref("bista_purchase.email_template_purchase_tracking")
        ctx = dict(self.env.context or {})
        try:
            compose_form_id = self.env.ref("mail.email_compose_message_wizard_form").id
        except ValueError:
            compose_form_id = False
        ctx.update(
            {
                "default_model": "purchase.tracking",
                "active_model": "purchase.tracking",
                "active_id": self.id,
                "default_res_id": self.id,
                "default_use_template": bool(template_id.id),
                "default_template_id": template_id.id,
                "default_composition_mode": "comment",
                "default_partner_ids": self.order_id.dest_address_id.ids,
                "custom_layout": "mail.mail_notification_paynow",
                "force_email": True,
            }
        )
        return {
            "name": _("Compose Email"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form_id, "form")],
            "view_id": compose_form_id,
            "target": "new",
            "context": ctx,
        }

    def edit_tracking_line(self):
        self.ensure_one()
        return {
            "name": _("Purchase Tracking Line"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.tracking",
            "view_mode": "form",
            "view_type": "form",
            "target": "new",
            "res_id": self.id,
            "view_id": self.env.ref("bista_purchase.purchase_tracking_form_view").id,
        }


class PurchaseTrackingRef(models.Model):
    _name = "purchase.tracking.ref"
    _description = "Purchase Tracking Ref"

    purchase_tracking_id = fields.Many2one("purchase.tracking")
    name = fields.Char(string="Number")
    tracking_url = fields.Char(
        string="Tracking URL", compute="_compute_tracking_url", store=True
    )

    @api.depends("name", "purchase_tracking_id.delivery_type")
    def _compute_tracking_url(self):
        for ref in self:
            if ref.purchase_tracking_id.delivery_type == "ups" and ref.name:
                ref.tracking_url = (
                    "http://wwwapps.ups.com/WebTracking/track?track=yes&trackNums=%s"
                    % ref.name.replace("+", "%0D%0A")
                )
            elif ref.purchase_tracking_id.delivery_type == "usps" and ref.name:
                ref.tracking_url = (
                    "https://tools.usps.com/go/TrackConfirmAction_input?qtc_tLabels1=%s"
                    % ref.name
                )


class PurchaseTrackingLine(models.Model):
    _name = "purchase.tracking.line"
    _description = "Purchase Tracking Line"

    checkbox = fields.Boolean(string="Checkbox")
    tracking_id = fields.Many2one(
        "purchase.tracking", string="Tracking", ondelete="cascade"
    )
    po_line_id = fields.Many2one("purchase.order.line", "PO Line")
    default_code = fields.Char(
        related="po_line_id.product_id.default_code", store=True, string="ISBN"
    )
    ordered_qty = fields.Float(
        related="po_line_id.product_qty", string="Ordered Quantity", store=True
    )
    received_qty = fields.Float(
        related="po_line_id.qty_received", string="Received Quantity", store=True
    )
    pending_shipment_qty = fields.Float(
        compute="_compute_quantities",
        string="Pending Shipment",
        store=False,
        compute_sudo=True,
    )
    ship_qty = fields.Float(string="Shipped Quantity")

    @api.depends("po_line_id", "ship_qty")
    def _compute_quantities(self):
        for line in self:
            tracking_line_ids = line.po_line_id.purchase_tracking_line_ids
            total_ship_qty = tracking_line_ids.filtered(
                lambda line: line.tracking_id.status != "cancel"
            ).mapped("ship_qty")
            line.pending_shipment_qty = line.ordered_qty - sum(total_ship_qty)

    @api.onchange("ship_qty")
    def _onchange_ship_qty(self):
        total_ship_qty = self.po_line_id.purchase_tracking_line_ids.filtered(
            lambda l: l.tracking_id.status != "cancel" and l.id != self._origin.id
        ).mapped("ship_qty")
        self.pending_shipment_qty = (
            self.ordered_qty - sum(total_ship_qty) - self.ship_qty
        )

    @api.onchange("checkbox")
    def _onchange_checkbox(self):
        if self.checkbox:
            self.ship_qty = self.pending_shipment_qty
