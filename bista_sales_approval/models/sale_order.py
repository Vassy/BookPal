# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2022 (https://www.bistasolutions.com)
#
##############################################################################
from datetime import datetime
from collections import defaultdict
from odoo import api, models, fields, _
from lxml import etree

AddState = [
    ("quote_approval", "Quotation In Approval"),
    ("quote_confirm", "Approved Quotation"),
    ("sent",),
    ("order_booked", "Order Booked"),
    ("pending_for_approval", "Order In Approval"),
    ("sale", "Approved Order"),
]
CustomFields = [
    "acquirer_ids",
    "user_id",
    "am_owner",
    "require_payment",
    "tag_ids",
    "opportunity_id",
    "refer_by_company",
    "refer_by_person",
    "origin",
    "medium_id",
    "source_id",
    "campaign_id",
    "order_notes",
    "gorgias_ticket",
    "product_status_notes",
    "product_use",
    "white_glove_id",
    "ce_notes",
    "am_notes",
    "ce_ops_acct_notes",
    "journal_customization_ids",
    "link_to_art_files",
    "journal_notes",
    "journal_setup_fee",
    "shipping_account",
    "so_shipping_cost",
    "artwork_status_id",
    "death_type_id",
    "existing_death_order",
    "customization_cost",
    "shipping_to",
    "potential_pallets",
    "accept_pallets",
    "has_loading_dock",
    "inside_delivery_req",
    "shipping_notes",
    "fulfilment_project",
    "project_description",
    "status_notes",
    "delivery_location",
    "project_status",
    "shipping_instruction",
    "customization_type_ids",
    "individual_mailer_return_address",
    "special_insert_note",
    "attachment_note",
    "book_status",
    "on_hold_reason",
    "recipient_list_status",
    "individual_mailer_return_receiver",
    "recipient_list_expected",
    "billing_notes",
    "payment_notes",
    "placed_from_ip",
    "customer_po_link",
    "is_report",
    "report_type",
    "report_notes",
    "report_date",
    "reported",
]


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = "Sales"

    state = fields.Selection(selection_add=AddState)
    sale_approval_log_ids = fields.One2many("sale.approval.log", "sale_id")
    is_order = fields.Boolean(copy=False)

    @api.depends("state")
    def _compute_type_name(self):
        states = ("draft", "quote_approval", "quote_confirm", "sent", "cancel")
        for record in self:
            record.type_name = (
                _("Quotation") if record.state in states else _("Sales Order")
            )

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        if self._context.get("order_booked"):
            result.update({"state": "order_booked", "is_order": True})
        return result

    def _prepare_confirmation_values(self):
        res = super()._prepare_confirmation_values()
        # Order Date should not change in any state
        if res.get("date_order"):
            res.pop("date_order")
        return res

    def trigger_quote_action(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "sale.action_quotations_with_onboarding"
        )
        if self.env.user.has_group("bista_sales_approval.group_approve_sale_quote"):
            action["context"] = {"search_default_quote_approval": 1}
        return action

    def trigger_order_action(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action["context"] = {"order_booked": True}
        if self.env.user.has_group("bista_sales_approval.group_approve_sale_order"):
            action["context"].update({"search_default_order_approval": 1})
        elif self.env.user.has_group("bista_sales_approval.group_create_sale_order"):
            action["context"].update({"search_default_booked_order": 1})
        return action

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get("mark_so_as_sent"):
            self.filtered(lambda o: o.state == "quote_confirm").with_context(
                tracking_disable=True
            ).write({"state": "sent"})
        return super().message_post(**kwargs)

    def has_to_be_signed(self, include_draft=False):
        display_state = ("quote_confirm", "sent", "order_booked", "sale")
        return (
            (self.state in display_state or (self.state == "draft" and include_draft))
            and not self.is_expired
            and self.require_signature
            and not self.signature
        )

    def has_to_be_paid(self, include_draft=False):
        transaction = self.get_portal_last_transaction()
        display_state = ("quote_confirm", "sent", "order_booked", "sale")
        return (
            (self.state in display_state or (self.state == "draft" and include_draft))
            and not self.is_expired
            and self.require_payment
            and transaction.state != "done"
            and self.amount_total
            and not self.transaction_ids.filtered(
                lambda t: t.state not in ("draft", "cancel", "error")
            )
        )

    def write(self, vals):
        if vals.get("state") and vals.get("state") == "sent":
            self._create_sale_approval_log("Quote Sent to Customer")
        return super().write(vals)

    def action_order_booked(self):
        for sale in self:
            if sale.state == "sale":
                continue
            sale_data = {
                "state": "order_booked",
                "is_order": True,
                "date_order": fields.Datetime.now(),
            }
            if sale.split_shipment:
                sale.sale_multi_ship_qty_lines.write({"state": "order_booked"})
            sale.write(sale_data)
            sale._create_sale_approval_log("Sale Order Booked")

    def action_send_quote_approval(self):
        for sale in self:
            sale.state = "quote_approval"
            sale._create_sale_approval_log("Quote Sent for Approval")

    def action_quote_confirm(self):
        approve_template = self.env.ref(
            "bista_sales_approval.email_template_sale_quote_approve"
        )
        for sale in self:
            self.state = "quote_confirm"
            approve_template.send_mail(sale.id, force_send=True)
            sale._create_sale_approval_log("Quote Confirmed")
            quote_approve_days = datetime.now().date() - sale.date_order.date()
            quote_days = quote_approve_days.days
            sale.quote_processing_time = str(quote_days) + " Days"

    def action_send_for_approval(self):
        for rec in self:
            rec.state = "pending_for_approval"
            rec._create_sale_approval_log("Order Sent for Approval")

    def action_approval(self):
        for rec in self:
            rec.action_confirm()
            rec._create_sale_approval_log("Order Approved")

    def action_reject(self):
        return {
            "name": "Reject Reason",
            "view_mode": "form",
            "res_model": "reject.reason.wiz",
            "type": "ir.actions.act_window",
            "context": {"default_sale_id": self.id},
            "target": "new",
        }

    def action_cancel(self):
        for sale in self:
            if sale.state == "sale":
                sale.is_order = True
        res = super().action_cancel()
        self._create_sale_approval_log("Cancelled")
        return res

    def _create_sale_approval_log(self, action):
        self.env["sale.approval.log"].create(
            {"sale_id": self.id, "done_action": action}
        )

    @api.model
    def _fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super()._fields_view_get(view_id, view_type, toolbar, submenu)
        if view_type != "form":
            return result
        custom_attrs = "{'readonly': [('state', 'in', ['sale', 'done', 'cancel'])]}"
        split = "{'invisible': [('state', 'in', ['draft', 'quote_approval', 'quote_confirm', 'sent', 'cancel'])]}"
        if self.env.user.has_group("bista_sales_approval.group_approve_sale_order"):
            attrs = "{'readonly': [('state', 'in', ['sale', 'done', 'cancel'])]}"
            custom_attrs = "{'readonly': [('state', 'in', ['done', 'cancel'])]}"
            split = "{'invisible': [('state', 'in', ['draft', 'quote_approval', 'quote_confirm', 'sent', 'cancel'])], 'readonly': [('state', 'in', ['sale', 'done', 'cancel'])]}"
        elif self.env.user.has_group("bista_sales_approval.group_create_sale_order"):
            attrs = "{'readonly': [('state', 'in', ['pending_for_approval', 'sale', 'done', 'cancel'])]}"
            split = "{'invisible': [('state', 'in', ['draft', 'quote_approval', 'quote_confirm', 'sent', 'cancel'])], 'readonly': [('state', 'in', ['pending_for_approval', 'sale', 'done', 'cancel'])]}"
        elif self.env.user.has_group("bista_sales_approval.group_approve_sale_quote"):
            attrs = "{'readonly': [('state', 'not in', ['draft', 'quote_approval'])]}"
        else:
            attrs = "{'readonly': [('state', 'not in', ['draft'])]}"
        doc = etree.XML(result["arch"])
        for field in doc.xpath("//field"):
            if field.attrib["name"] in ["purchase_order_count"]:
                field.attrib["readonly"] = "1"
                continue
            if field.attrib["name"] in CustomFields:
                field.attrib["attrs"] = custom_attrs
                continue
            if field.attrib["name"] in ["split_shipment"]:
                field.attrib["attrs"] = split
                continue
            if field.attrib["name"] in [
                "order_line",
                "partner_shipping_id",
                "validity_date",
                "date_order",
                "supplier_id",
                "customer_lead",
                "analytic_account_id",
            ]:
                field.attrib["attrs"] = attrs
            if (
                field.attrib.get("invisible") == "1"
                or field.attrib.get("readonly") == "1"
                or field.attrib["name"] not in self._fields
                or field.attrib.get("attrs")
                or field.attrib["name"] == "sale_multi_ship_qty_lines"
                or field.attrib["name"] in ["customer_po_link", "book_use_email", "approved_by_am", "shipping_quote_docs"]
            ):
                continue
            field.attrib["attrs"] = attrs
        result["arch"] = etree.tostring(doc)
        return result


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # Override method to display qty widget on custom status.
    @api.depends(
        "product_type",
        "product_uom_qty",
        "qty_delivered",
        "state",
        "move_ids",
        "product_uom",
    )
    def _compute_qty_to_deliver(self):
        """Compute the visibility of the inventory widget."""
        for line in self:
            line.qty_to_deliver = line.product_uom_qty - line.qty_delivered
            if (
                line.state not in ("done", "cancel")
                and line.product_type == "product"
                and line.product_uom
                and line.qty_to_deliver > 0
            ):
                if line.state == "sale" and not line.move_ids:
                    line.display_qty_widget = False
                else:
                    line.display_qty_widget = True
            else:
                line.display_qty_widget = False

    @api.depends(
        "product_id",
        "customer_lead",
        "product_uom_qty",
        "product_uom",
        "order_id.commitment_date",
        "move_ids",
        "move_ids.forecast_expected_date",
        "move_ids.forecast_availability",
    )
    def _compute_qty_at_date(self):
        """Compute the quantity forecasted of product at delivery date. There are
        two cases:
         1. The quotation has a commitment_date, we take it as delivery date
         2. The quotation hasn't commitment_date, we compute the estimated delivery
            date based on lead time"""
        treated = self.browse()
        # If the state is already in sale the picking is created and a simple forecasted
        # quantity isn't enough Then used the forecasted data of the related stock.move
        for line in self.filtered(lambda l: l.state == "sale"):
            if not line.display_qty_widget:
                continue
            moves = line.move_ids.filtered(lambda m: m.product_id == line.product_id)
            line.forecast_expected_date = max(
                moves.filtered("forecast_expected_date").mapped(
                    "forecast_expected_date"
                ),
                default=False,
            )
            line.qty_available_today = 0
            line.free_qty_today = 0
            for move in moves:
                line.qty_available_today += move.product_uom._compute_quantity(
                    move.reserved_availability, line.product_uom
                )
                line.free_qty_today += move.product_id.uom_id._compute_quantity(
                    move.forecast_availability, line.product_uom
                )
            line.scheduled_date = line.order_id.commitment_date or line._expected_date()
            line.virtual_available_at_date = False
            treated |= line

        qty_processed_per_product = defaultdict(lambda: 0)
        grouped_lines = defaultdict(lambda: self.env["sale.order.line"])
        # We first loop over the SO lines to group them by warehouse and schedule
        # date in order to batch the read of the quantities computed field.
        """ Bug #18863 - Override code for display proper stock qty widget """
        for line in self.filtered(lambda l: l.state not in ("sale", "done", "cancel")):
            if not (line.product_id and line.display_qty_widget):
                continue
            grouped_lines[
                (
                    line.warehouse_id.id,
                    line.order_id.commitment_date or line._expected_date(),
                )
            ] |= line

        for (warehouse, scheduled_date), lines in grouped_lines.items():
            product_qties = (
                lines.mapped("product_id")
                .with_context(to_date=scheduled_date, warehouse=warehouse)
                .read(
                    [
                        "qty_available",
                        "free_qty",
                        "virtual_available",
                    ]
                )
            )
            qties_per_product = {
                product["id"]: (
                    product["qty_available"],
                    product["free_qty"],
                    product["virtual_available"],
                )
                for product in product_qties
            }
            for line in lines:
                line.scheduled_date = scheduled_date
                (
                    qty_available_today,
                    free_qty_today,
                    virtual_available_at_date,
                ) = qties_per_product[line.product_id.id]
                line.qty_available_today = (
                    qty_available_today - qty_processed_per_product[line.product_id.id]
                )
                line.free_qty_today = (
                    free_qty_today - qty_processed_per_product[line.product_id.id]
                )
                line.virtual_available_at_date = (
                    virtual_available_at_date
                    - qty_processed_per_product[line.product_id.id]
                )
                line.forecast_expected_date = False
                product_qty = line.product_uom_qty
                if (
                    line.product_uom
                    and line.product_id.uom_id
                    and line.product_uom != line.product_id.uom_id
                ):
                    line.qty_available_today = line.product_id.uom_id._compute_quantity(
                        line.qty_available_today, line.product_uom
                    )
                    line.free_qty_today = line.product_id.uom_id._compute_quantity(
                        line.free_qty_today, line.product_uom
                    )
                    line.virtual_available_at_date = (
                        line.product_id.uom_id._compute_quantity(
                            line.virtual_available_at_date, line.product_uom
                        )
                    )
                    product_qty = line.product_uom._compute_quantity(
                        product_qty, line.product_id.uom_id
                    )
                qty_processed_per_product[line.product_id.id] += product_qty
            treated |= lines
        remaining = self - treated
        remaining.virtual_available_at_date = False
        remaining.scheduled_date = False
        remaining.forecast_expected_date = False
        remaining.free_qty_today = False
        remaining.qty_available_today = False


class SaleApprovalLog(models.Model):
    _name = "sale.approval.log"
    _description = "Log information of Sale Order Approval Process"

    sale_id = fields.Many2one("sale.order", ondelete="cascade")
    note = fields.Text(string="Reason")
    done_action = fields.Char(string="Performed Action")
    action_user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.uid
    )
    action_date = fields.Datetime(string="Date", default=fields.Datetime.now)
