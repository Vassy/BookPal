# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):
    _inherit = "sale.order"

    white_glove_id = fields.Many2one("white.glove.type", string="White Glove")
    event_date = fields.Date(string="Event Date")
    order_notes = fields.Text(string="Order Notes")
    product_status_notes = fields.Text(string="Product Status Notes")
    gorgias_ticket = fields.Text(string="Gorgias Ticket")
    ce_notes = fields.Text(string="CE Notes")
    payment_notes = fields.Text(string="Payment Notes")
    am_notes = fields.Text(string="AM Notes")
    approved_by_am = fields.Boolean(string="Approved by AM to Process")
    ce_ops_acct_notes = fields.Text(string="CE-Ops Acct Notes")
    billing_notes = fields.Text(
        string="Billing Notes",
        default=lambda self: self.opportunity_id
        and self.opportunity_id.payment_notes
        or "",
    )
    placed_from_ip = fields.Char(string="Placed from IP")
    # journal or promotional product fields
    journal_customization_ids = fields.Many2many(
        "journal.customization", string="Journal Customization"
    )
    customization_cost = fields.Monetary("Our Customization Cost")
    link_to_art_files = fields.Char(string="Link to Art Files")
    artwork_status_id = fields.Many2one("artwork.status", string="Artwork Status")
    journal_notes = fields.Text(string="Journal Notes")
    journal_setup_fee = fields.Selection(
        [("waived", "Waived"), ("75", "$75.00")], string="Journal Set Up Fee"
    )
    shipping_account = fields.Selection(
        [("our_account", "Our Account"), ("castelli_account", "Castelli's Account")],
        string="Shipping Account",
    )
    so_shipping_cost = fields.Monetary(string=" Our Shipping Cost")
    death_type_id = fields.Many2one("death.type", string="Die Type")
    existing_death_order = fields.Text(string="Existing Die Order #")
    # Shipping Info.
    shipping_notes = fields.Text(string="Shipping Notes")
    shipping_to = fields.Boolean("Shipping to Hotel or Event Venue")
    potential_pallets = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Potential Pallets"
    )
    accept_pallets = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Accept Pallets"
    )
    has_loading_dock = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Has Loading Dock"
    )
    inside_delivery_req = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Inside Delivery Required"
    )
    # Project & Fulfilment Tracking.
    fulfilment_project = fields.Boolean("Fulfillment Project")
    am_owner = fields.Many2one("res.users", string="Ops Owner")
    project_description = fields.Text(string="Project Description")
    project_status = fields.Text(string="Project Status")
    status_notes = fields.Text(string="Status Notes")
    delivery_location = fields.Selection(
        [
            ("domestic", "Domestic"),
            ("international", "International"),
            ("domestic_int", "Domestic/International"),
        ],
        string="Delivery Location",
    )
    shipping_instruction = fields.Text(string="Shipping Instruction")
    customization_type_ids = fields.Many2many(
        "customization.type", string="Customization Type"
    )
    special_insert_note = fields.Text(string="Special Insert Notes")
    attachment_note = fields.Text(string="Attachment Notes")
    individual_mailer_return_receiver = fields.Text(
        string="Individual Mailer Return Receiver"
    )
    recipient_list_status = fields.Text(string="Recipient List Status")
    recipient_list_expected = fields.Text(string="Recipient List Expected")
    individual_mailer_return_address = fields.Text(
        string="Individual Mailer Return Address"
    )
    book_status = fields.Text(string="Book Status")
    on_hold_reason = fields.Text(string="On Hold Reason(s)")
    due_amount = fields.Monetary("Due Amount", related="partner_id.total_due")

    refer_by_company = fields.Many2one("res.partner", string="Referring Organization")
    refer_by_person = fields.Many2one("res.partner", string="Referring Person")
    account_order_standing = fields.Selection(
        related="partner_id.account_order_standing", store=True
    )
    saving_amount = fields.Monetary(
        "Total Saving Amount", compute="_amount_all", store=True
    )
    is_report = fields.Boolean(string="Report", default=True, tracking=True)
    reason = fields.Char(string="Reason")
    report_type = fields.Selection(
        [("individual", "Individual"), ("bulk", "Bulk"), ("mixed", "Mixed")],
        string="Report Type",
    )
    report_notes = fields.Text(string="Reporting Notes")
    quote_processing_time = fields.Char(
        string="Quotation Process Days", default="0 Days"
    )
    product_weight = fields.Float(
        compute="_compute_product_weight", string="Product Weight"
    )
    weight_uom_name = fields.Char(
        string="Weight unit of measure label", compute="_compute_weight_uom"
    )
    product_use = fields.Text(string="Product Use")
    acquirer_ids = fields.Many2many(
        "payment.acquirer",
        string="Available Payments",
        domain=lambda self: self._get_available_acquirer(),
    )
    customer_po_link = fields.Char("Customer PO Link")
    book_use_email = fields.Char()
    shipping_quote_docs = fields.Char()
    share_link = fields.Char(string="Link", compute="_compute_share_link")
    button_name = fields.Char(compute="_compute_button_name")
    ontime_status = fields.Selection(
        [("yes", "Yes"), ("no", "Delayed"), ("pending", "Pending")],
        compute="_compute_order_process_time",
        string="On Time Status",
        store=True,
        compute_sudo=True,
    )
    order_delivery_time = fields.Char(
        compute="_compute_order_process_time", string="Order Delivery Time", store=True
    )
    last_delivery_date = fields.Date(
        compute="_compute_last_del_date", store=True, compute_sudo=True
    )
    delivery_time = fields.Integer(compute="_compute_order_process_time", store=True)
    report_date = fields.Date(
        string="Report Date", compute="_compute_report_date", store=True
    )
    reported = fields.Boolean(string="Reported")
    commitment_date = fields.Datetime(
        string="Need By Date", compute="_compute_commitment_date", store=True
    )

    @api.depends("date_order")
    def _compute_commitment_date(self):
        for sale in self:
            sale.commitment_date = sale.date_order + relativedelta(days=7)

    @api.depends("date_order", "order_line", "order_line.product_id.publication_date")
    def _compute_report_date(self):
        for sale in self:
            max_date = (
                sale.order_line.mapped("product_id")
                .filtered(lambda p: p.publication_date)
                .mapped("publication_date")
            )
            if max_date and max(max_date) > fields.Date.today():
                sale.report_date = max(max_date) + relativedelta(
                    days=-max(max_date).weekday(), weeks=1
                )
            else:
                sale.report_date = sale.date_order + relativedelta(
                    days=-sale.date_order.weekday(), weeks=1
                )

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = super()._find_mail_template(force_confirmation_template)
        if not force_confirmation_template and self._context.get("sale_invoice"):
            template_id = self.env["ir.model.data"]._xmlid_to_res_id(
                "sale.email_template_edi_sale", raise_if_not_found=False
            )
        return template_id

    @api.depends("picking_ids", "picking_ids.date_done")
    def _compute_last_del_date(self):
        for rec in self:
            last_delivery_date_new = False
            last_delivery_date_list = []
            return_pickings = rec.picking_ids.filtered(
                lambda x: x.origin and "Return of" in x.origin
            )
            picking_ids = rec.picking_ids - return_pickings
            for picking in picking_ids:
                last_delivery_date = picking.date_done
                if last_delivery_date:
                    last_delivery_date_list.append(
                        last_delivery_date.date().strftime("%Y-%m-%d")
                    )
            if len(last_delivery_date_list) >= 1:
                last_delivery_date_new = max(last_delivery_date_list)
            rec.last_delivery_date = last_delivery_date_new

    @api.depends("commitment_date", "last_delivery_date")
    def _compute_order_process_time(self):
        for rec in self:
            if rec.commitment_date and not rec.last_delivery_date:
                rec.ontime_status = "pending"
            if rec.last_delivery_date and rec.commitment_date:
                if rec.last_delivery_date < rec.commitment_date.date():
                    days = (rec.commitment_date.date() - rec.last_delivery_date).days
                    rec.order_delivery_time = "-" + str(days) + " Days"
                    rec.ontime_status = "yes"
                    rec.delivery_time = (
                        rec.last_delivery_date - rec.commitment_date.date()
                    ).days
                if rec.last_delivery_date > rec.commitment_date.date():
                    rec.order_delivery_time = (
                        str((rec.last_delivery_date - rec.commitment_date.date()).days)
                        + " Days"
                    )
                    rec.ontime_status = "no"
                    rec.delivery_time = (
                        rec.last_delivery_date - rec.commitment_date.date()
                    ).days

    def _compute_share_link(self):
        for rec in self:
            rec.share_link = rec.get_base_url() + rec._get_share_url(redirect=True)

    @api.depends("name")
    def _compute_button_name(self):
        for rec in self:
            rec.button_name = "View " + str(rec.name)

    def write(self, vals):
        """Skip to update salesperson automatically."""
        if not self._context.get("manual_update") and "user_id" in vals:
            vals.pop("user_id")
        res = super(SaleOrder, self).write(vals)
        return res

    def _get_available_acquirer(self):
        payment = self.env["payment.acquirer"].sudo()
        payment_ids = payment._get_compatible_acquirers(
            company_id=self.env.company.id,
            partner_id=self.env.user.partner_id.id,
        )
        return [("id", "in", payment_ids.ids)]

    @api.depends("order_line.price_total")
    def _amount_all(self):
        super()._amount_all()
        for sale in self:
            sale.saving_amount = sum(sale.order_line.mapped("saving_amount"))

    @api.depends("picking_ids.is_dropship")
    def _compute_picking_ids(self):
        super()._compute_picking_ids()
        for order in self:
            order.delivery_count -= len(
                order.picking_ids.filtered(lambda p: p.sequence_code in ["IN", "INT"])
            )

    def action_view_delivery(self):
        return self._get_action_view_picking(
            self.picking_ids.filtered(
                lambda p: not p.is_dropship and p.sequence_code not in ["IN", "INT"]
            )
        )

    @api.constrains("journal_setup_fee", "customization_cost", "so_shipping_cost")
    def warning_journal_setup_fee(self):
        if self.customization_cost < 0:
            raise ValidationError(
                "customization cost value is negative,add positive value."
            )
        if self.so_shipping_cost < 0:
            raise ValidationError(
                "shipping cost  value is negative,add positive value."
            )

    @api.onchange("fulfilment_project")
    def onchange_fulfilment_project(self):
        if self.fulfilment_project:
            self.report_type = "individual"

    @api.depends("order_line.product_uom_qty", "order_line.product_id")
    def _compute_product_weight(self):
        for order in self:
            final_weight = sum(
                line.product_id.weight * line.product_uom_qty
                for line in order.order_line.filtered(
                    lambda l: l.product_id and l.product_id.type in ("product")
                )
            )
        order.product_weight = final_weight

    def _compute_weight_uom(self):
        self.weight_uom_name = self.env[
            "product.template"
        ]._get_weight_uom_name_from_ir_config_parameter()

    def action_open_delivery_wizard(self):
        res = super(SaleOrder, self).action_open_delivery_wizard()
        if self.opportunity_id.carrier_id.id:
            res["context"].update(
                {"default_carrier_id": self.opportunity_id.carrier_id.id}
            )
        return res

    @api.onchange("user_id")
    def onchange_user_id(self):
        if self.user_id and self.env.context.get("manual_update"):
            self._origin.with_context(manual_update=True).write(
                {"user_id": self.user_id.id}
            )
        if self.user_id:
            default_team = (
                self.env.context.get("default_team_id", False) or self.team_id.id
            )
            self.team_id = (
                self.env["crm.team"]
                .with_context(default_team_id=default_team)
                ._get_default_team_id(user_id=self.user_id.id, domain=None)
            )

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        user_id = self.user_id
        super(SaleOrder, self).onchange_partner_id()
        if user_id:
            self.user_id = user_id
        if self.partner_id and not self._context.get("no_change_refer"):
            self.refer_by_person = self.partner_id.referal_source.id
            self.refer_by_company = self.partner_id.referring_organization.id
        self.acquirer_ids = self.partner_id.acquirer_ids.ids


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def default_get(self, fields):
        defaults = super().default_get(fields)
        defaults["route_id"] = self.env.ref("stock_dropshipping.route_drop_shipping").id
        return defaults

    tracking_ref = fields.Char("Tracking Refrence", compute="get_tracking_ref")
    saving_amount = fields.Float("Saving Amount", compute="_compute_amount", store=True)
    discounted_price = fields.Float(
        "Quote Price", compute="_compute_prices", store=True, readonly=False
    )
    discount = fields.Float(compute="_compute_discount", store=True, readonly=False)
    attachment_ids = fields.Many2many("ir.attachment", string="Attach File")
    detailed_type = fields.Selection(related="product_id.detailed_type")

    def _check_line_unlink(self):
        """Overwritten method to not delete line in order booked state."""
        undeletable_lines = self.filtered(
            lambda line: line.state in ("sale", "order_booked", "done")
            and (line.invoice_lines or not line.is_downpayment)
            and not line.display_type
        )
        return undeletable_lines.filtered(lambda line: not line.is_delivery)

    @api.depends(
        "product_uom_qty", "discount", "price_unit", "tax_id", "discounted_price"
    )
    def _compute_amount(self):
        for line in self:
            discount = line.discount
            if line.price_unit:
                discount = 100 - (line.discounted_price / line.price_unit * 100)
            price = line.price_unit * (1 - (discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(
                price,
                line.order_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id,
            )
            saving_amount = 0
            if line.discount:
                saving_amount = line.price_unit * discount / 100 * line.product_uom_qty
            line.update(
                {
                    "price_tax": sum(
                        t.get("amount", 0.0) for t in taxes.get("taxes", [])
                    ),
                    "price_total": taxes["total_included"],
                    "price_subtotal": taxes["total_excluded"],
                    "saving_amount": saving_amount,
                }
            )

    @api.depends("price_unit", "discount")
    def _compute_prices(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.currency_id:
                line.discounted_price = line.currency_id.round(price)

    @api.depends("price_unit", "discounted_price")
    def _compute_discount(self):
        for line in self:
            discount = 0
            if line.price_unit:
                discount = 100 - (line.discounted_price / line.price_unit * 100)
            line.discount = discount

    @api.depends("move_ids.state")
    def get_tracking_ref(self):
        """Get the tracking reference."""
        for line in self:
            tracking_ref = (
                line.move_ids.filtered(
                    lambda x: x.picking_type_id.code in ["outgoing", "incoming"]
                    and x.quantity_done
                )
                .mapped("picking_id")
                .mapped("carrier_tracking_ref")
            )
            tracking_ref = ", ".join([str(elem) for elem in tracking_ref if elem])
            line.tracking_ref = tracking_ref

    @api.onchange("product_id")
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.product_id:
            vendor = self.product_id._prepare_sellers({}).filtered(
                lambda s: not s.company_id or s.company_id == self.company_id
            )[:1]
            if vendor:
                self.supplier_id = (
                    vendor.filtered(lambda x: x.name.is_primary).name.id
                    if vendor.filtered(lambda x: x.name.is_primary)
                    else vendor[:1].name.id
                )
        return res

    @api.model
    def create(self, vals_list):
        """Fix attachment ownership."""
        rec = super(SaleOrderLine, self).create(vals_list)
        if rec.attachment_ids:
            rec.attachment_ids.write({"res_model": self._name, "res_id": rec.id})
        return rec

    def _get_outgoing_incoming_moves(self):
        outgoing_moves = self.env["stock.move"]
        incoming_moves = self.env["stock.move"]
        moves = self.move_ids.filtered(
            lambda r: r.state != "cancel"
            and not r.scrapped
            and self.product_id == r.product_id
            and r.picking_code in ["outgoing", "incoming"]
        )
        if self._context.get("accrual_entry_date"):
            moves = moves.filtered(
                lambda r: fields.Date.context_today(r, r.date)
                <= self._context["accrual_entry_date"]
            )
        for move in moves:
            if move.location_dest_id.usage == "customer":
                if not move.origin_returned_move_id or (
                    move.origin_returned_move_id and move.to_refund
                ):
                    outgoing_moves |= move
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                incoming_moves |= move
        return outgoing_moves, incoming_moves
