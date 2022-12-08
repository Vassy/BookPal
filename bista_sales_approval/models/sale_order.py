# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2022 (https://www.bistasolutions.com)
#
##############################################################################

from odoo import api, models, fields
from lxml import etree

AddState = [
    ("quote_approval", "Quotation Approval"),
    ("quote_confirm", "Quotation Confirmed"),
    ("sent",),
    ("customer_approved", "Customer Approved"),
    ("pending_for_approval", "Pending for Approval"),
    ("sale",),
]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(selection_add=AddState)
    sale_approval_log_ids = fields.One2many("sale.approval.log", "sale_id")

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get("mark_so_as_sent"):
            self.filtered(lambda o: o.state == "quote_confirm").with_context(
                tracking_disable=True
            ).write({"state": "sent"})
        return super().message_post(**kwargs)

    def has_to_be_signed(self, include_draft=False):
        display_state = self.state == "sent" or (
            self.state in ["draft", "quote_approval", "quote_confirm"] and include_draft
        )
        return (
            display_state
            and not self.is_expired
            and self.require_signature
            and not self.signature
        )

    def has_to_be_paid(self, include_draft=False):
        transaction = self.get_portal_last_transaction()
        display_state = self.state == "sent" or (
            self.state in ["draft", "quote_approval", "quote_confirm"] and include_draft
        )
        return (
            display_state
            and not self.is_expired
            and self.require_payment
            and transaction.state != "done"
            and self.amount_total
        )

    def write(self, vals):
        if vals.get("state") and vals.get("state") == "sent":
            self._create_sale_approval_log("Quote Sent to Customer")
        return super().write(vals)

    def action_send_quote_approval(self):
        for sale in self:
            sale.state = "quote_approval"
            sale._create_sale_approval_log("Quote Sent for Approval")

    def action_quote_confirm(self):
        for sale in self:
            sale.state = "quote_confirm"
            sale._create_sale_approval_log("Quote Confirmed")

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
        attrs = "{'readonly': [('state', 'not in', ['draft', 'sent'])]}"
        line_attrs = "{'readonly': [('state', 'not in', ['draft'])]}"
        if self.env.user.has_group("bista_sales_approval.group_sale_approval_admin"):
            attrs = "{'readonly': [('state', 'not in', ['draft', 'sent', 'pending_for_approval'])]}"
            line_attrs = "{'readonly': [('state', 'in', ['done', 'cancel'])]}"
        doc = etree.XML(result["arch"])
        for field in doc.xpath("//field"):
            if field.attrib["name"] == "order_line":
                field.attrib["attrs"] = line_attrs
            if (
                field.attrib.get("invisible") == "1"
                or field.attrib.get("readonly") == "1"
                or field.attrib.get("attrs")
                or field.attrib["name"] not in self._fields
            ):
                continue
            field.attrib["attrs"] = attrs
        result["arch"] = etree.tostring(doc)
        return result


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
