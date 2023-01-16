# -*- coding: utf-8 -*-

import datetime

from lxml import etree

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from odoo.tools import is_html_empty

AddState = [
        ('draft', 'Purchase Order'),
        ('sent', 'Order Sent'),
        ('to approve', 'To Approve'),
        ('reject', 'Rejected'),
        ('purchase', 'Approved Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ]

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # po_name = fields.Char(string="Purchase Order Name", related="name")
    po_conf = fields.Text(string='PO Conf #')
    clock_start_override = fields.Date(string='Clock Starts Override')
    clock_override_reason = fields.Text(string='Clock Starts Override Reason')
    hours_process = fields.Char(string='Hours to Process')

    # Review Order Notes and Requirements
    status = fields.Many2one('purchase.line.status', string='Status')
    order_notes = fields.Text(string='Order Notes')
    fulfilment_project = fields.Boolean(string="Fulfillment Project")
    ordered_by = fields.Many2one(
        related="order_line.partner_id", string="Ordered By")
    ops_project_owner_id = fields.Many2one(
        'res.users', string='Ops Project Owner')
    # billing_notes = fields.Text(string="Billing Notes")
    # cc_email = fields.Char(string="CC Email")
    supplier_nuances = fields.Text(
        string="Supplier Nuances", related="partner_id.supplier_nuances")
    minimum_nuances = fields.Text(
        string="Minimums Nuances", related="partner_id.minimums_nuances")
    pre_approval_nuances = fields.Text(
        string="Pre Approval Nuances", related="partner_id.pre_approval_nuances")
    transfer_to_bookpal_warehouse = fields.Boolean(
        string="Transfer to BookPal Warehouse")
    type = fields.Selection([('customer', 'Customer'),
                             ('supplier', 'Supplier'),
                             ('credit', 'Credit'),
                             ], string="Type")
    supplier_warehouse = fields.Many2one(
        'stock.warehouse', string='Supplier Warehouse')

    future_ship_nuances = fields.Text(
        string="Future Ship Nuances", related="partner_id.future_ship_nuances")
    shipping_nuances = fields.Text(
        string="Shipping Nuances", related="partner_id.shipping_nuances")
    processing_time_nuances = fields.Text(string="Processing Time Nuances",
                                          related="partner_id.processing_time_nuances")
    author_event_naunces = fields.Text(
        string="Author Event Nuances", related="partner_id.author_event_naunces")
    author_event_shipping_naunces = fields.Text(string="Author Event Shipping Nuances",
                                                related="partner_id.author_event_shipping_naunces")
    rush_status_id = fields.Many2one('rush.status', string='Rush Status')
    shipping_instructions = fields.Many2one('shipping.instruction', string='Shipping Instructions')
    order_shipping_desc = fields.Text(string='Order Shipping Description', related="partner_id.shipping_notes")
    default_supplier_shipping = fields.Many2one(string='Default Supplier Shipping',
                                                related="partner_id.default_shipping_id")
    freight_charges = fields.Float(string='Freight Charges', related="partner_id.default_frieght_charges")
    rush_shipping_nuances = fields.Text(
        string="Rush Shipping Nuances", related="partner_id.rush_processing_nuances")
    shipping_acct_nuances = fields.Text(
        string="Shipping Acct Nuances", related="partner_id.shipping_acct_nuances")
    freight_nuances = fields.Text(
        string="Freight Nuances", related="partner_id.frieght_nuances")
    opening_text_nuances = fields.Text(
        string="Opening Text Nuances", related="partner_id.opening_text_nuances")
    note_to_vendor_nuances = fields.Text(
        string="Note to Vendor Nuances", related="partner_id.note_to_vendor_nuances")
    memo = fields.Text(string="Memo")
    supplier_order_number = fields.Char(string="Supplier Order Number")
    num_of_need_by_days = fields.Text(string='Num of Need By Days')
    need_by_date = fields.Date(string="Need By Date")
    sale_order_ids = fields.Many2many(
        'sale.order', compute="compute_sale_order_ids")
    purchase_tracking_ids = fields.One2many(
        'purchase.tracking', 'order_id', string="Purchase Tracking")
    lead_time = fields.Integer(compute="compute_lead_time", string="Lead Time")
    order_process_time = fields.Integer(
        compute="compute_order_process_time", string="Order Processing Time")
    purchase_approval_log_ids = fields.One2many("purchase.approval.log", "order_id")
    state = fields.Selection(selection_add=AddState)
    is_email_sent = fields.Boolean(string="Email Sent", default=False)

    def action_rfq_send(self):
        result = super().action_rfq_send()
        event_glove = self.env.ref("bista_sale.white_glove_type")
        if event_glove in self.sale_order_ids.mapped("white_glove_id"):
            cc_partner_ids = self.partner_id.child_ids.filtered(lambda p: p.is_primary)
            cc_partner_ids |= self.partner_id.child_ids.filtered(lambda p: event_glove in p.glove_type_ids)
            result["context"].update({"default_cc_partner_ids": cc_partner_ids.ids})
        return result

    def button_cancel(self):
        # Chanage orderline status on cancel order
        res = super(PurchaseOrder, self).button_cancel()
        cancel_status_id = self.env.ref('bista_purchase.status_line_canceled')
        for order in self:
            order.order_line.write({'status_id': cancel_status_id.id})
        return res

    def button_draft(self):
        # change order line status on create and reset to draft order
        res = super(PurchaseOrder, self).button_draft()
        draft_status_id = self.env.ref('bista_purchase.status_line_draft')
        for order in self:
            order.order_line.write({'status_id': draft_status_id.id})
        return res

    def button_approve(self, force=False):
        # change order line status on confirm order
        ordered_status_id = self.env.ref('bista_purchase.status_line_ordered')
        self = self.filtered(lambda order: order._approval_allowed())
        self.order_line.write({'status_id': ordered_status_id.id})
        return super(PurchaseOrder, self).button_approve(force)

    def button_confirm(self):
        # change order line status on confirm order
        res = super(PurchaseOrder, self).button_confirm()
        ready_status_id = self.env.ref('bista_purchase.status_line_ready')
        if ready_status_id:
            for order in self:
                if not order._approval_allowed():
                    order.order_line.write({'status_id': ready_status_id.id})
        if not self.shipping_instructions:
            raise ValidationError(_('Please select the shipping instructions'))
        if is_html_empty(self.special_pick_note):
            raise ValidationError(_('Please add the Notes'))
        return res

    def _approval_allowed(self):
        """Returns whether the order qualifies to be approved by the current user"""
        self.ensure_one()
        if self._context.get('skip_approval'):
            return True
        return super(PurchaseOrder, self)._approval_allowed()

    def write(self, vals):
        if vals.get("state") and not self._context.get('no_history_update'):
            log_data = {
                "order_id": self.id,
                "old_state": self.state,
                "state": vals.get("state")
            }
            self.env["purchase.approval.log"].create(log_data)
        return super(PurchaseOrder, self).write(vals)

    def open_tracking(self):
        return {
            "name": _("Shipment Tracking"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.tracking",
            "view_mode": "form",
            "target": "new",
            "context": {"default_order_id": self.id},
        }

    def compute_sale_order_ids(self):
        for order_id in self:
            order_id.sale_order_ids = order_id._get_sale_orders()

    def update_po_lines(self):
        po_lines = self.env['purchase.order.line'].search(
            [('id', 'in', self.order_line.ids)])

        return {
            'name': _('Update PO Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'update.po.line',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_po_lines': po_lines.ids, 'default_order_id': self.id},
            'domain': (['id', 'in', po_lines.ids]),
        }

    # @api.onchange('partner_id')
    # def onchange_partner_id_cc_email(self):
    #     self.cc_email = self.partner_id.cc_email

    # def _prepare_picking(self):
    #     res = super(PurchaseOrder, self)._prepare_picking()
    #     res.update({'note': self.special_pick_note})
    #     return res

    @api.onchange('order_line')
    def onchange_product_is_exist(self):
        if self.order_line.product_id:
            prod_list = [line.product_id.id for line in self.order_line]
            for line in self.order_line:
                product_name = ''
                product_ref = '' if not line.product_id.default_code else '[' + line.product_id.default_code + '] '
                if prod_list.count(line.product_id.id) > 1:
                    product_name = product_ref + product_name + line.product_id.name
                    raise ValidationError(product_name + ' is already added in line, you can Update the qty there.')

    def compute_lead_time(self):
        for rec in self:
            rec.lead_time = 0
            if rec.date_approve:
                rec.lead_time = False
                date_list = rec.picking_ids.mapped('scheduled_date')
                val = sorted(date_list, reverse=True)
                if val:
                    date_time = val[0].date() - rec.date_approve.date()
                    rec.lead_time = date_time.days

    def compute_order_process_time(self):
        for rec in self:
            rec.order_process_time = 0
            if rec.sale_order_ids.split_shipment and rec.date_approve:
                rec.order_process_time = False
                vals = min(
                    rec.sale_order_ids.sale_multi_ship_qty_lines.mapped('confirm_date'))
                if vals:
                    rec_date = rec.date_approve - vals
                    rec.order_process_time = rec_date.days
            else:
                if rec.sale_order_ids.date_order and rec.date_approve:
                    order_date = rec.date_approve - rec.sale_order_ids.date_order
                    rec.order_process_time = order_date.days

    def action_send_for_approval(self):
        for rec in self:
            rec.state = "to approve"

    def button_reject(self):
        return {
            "name": "Reject Reason",
            "view_mode": "form",
            "res_model": "order.reject.wiz",
            "type": "ir.actions.act_window",
            "context": {"default_order_id": self.id},
            "target": "new",
        }

    @api.model
    def _fields_view_get(
            self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super()._fields_view_get(view_id, view_type, toolbar, submenu)
        if view_type != "form":
            return result
        doc = etree.XML(result["arch"])
        if not self.env.user.has_group("purchase.group_purchase_manager"):
            attrs = "{'readonly': [('state', 'not in', ['draft', 'sent'])]}"
            for field in doc.xpath("//field"):
                if (
                        field.attrib.get("invisible") == "1"
                        or field.attrib.get("readonly") == "1"
                        or field.attrib["name"] not in self._fields
                ):
                    continue
                field.attrib["attrs"] = attrs
        else:
            for node in doc.xpath("//button[@id='draft_confirm']"):
                node.set('invisible', "1")
        result["arch"] = etree.tostring(doc)
        return result

    @api.model
    def create(self, vals_list):
        """Create Purchase Order Approval History """
        rec = super(PurchaseOrder, self).create(vals_list)
        log_data = {
                "order_id": rec.id,
                "old_state": rec.state,
                "state": rec.state
            }
        self.env["purchase.approval.log"].create(log_data)
        return rec

    def trigger_rfq_action(self):
        """ server action to add filter according to user right for purchase order"""
        action = self.env["ir.actions.actions"]._for_xml_id(
            "purchase.purchase_rfq"
        )
        if self.env.user.has_group("purchase.group_purchase_manager"):
            action["context"] = {"search_default_to_approve": 1}
        elif self.env.user.has_group(
            "purchase.group_purchase_user"):
            action["context"] = {
                "search_default_draft_rfqs": 1,
            }
        return action

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        rec = super(PurchaseOrder, self).message_post(**kwargs)
        if self.env.context.get('mark_rfq_as_sent'):
            self.is_email_sent = True
            self.filtered(lambda o: o.state == 'sent').write({'state': 'draft'})
        return rec

    def print_quotation(self):
        return self.env.ref('purchase.report_purchase_quotation').report_action(self)

    @api.constrains('date_approve', 'date_planned')
    def warning_on_reciept_date(self):
        for order in self:
            if order.state == 'purchase':
                if order.date_planned.date() and (order.date_planned.date() < order.date_approve.date()):
                    raise ValidationError(_('Receipt date cannot be earlier than confirmation date'))

class RushStatus(models.Model):
    _name = "rush.status"
    _description = 'Rush Status model details.'
    _order = "sequence"

    name = fields.Char('Name')
    sequence = fields.Integer(string="Sequence", default=0)
    active = fields.Boolean(string="Archived", default=True)


class ShippingInstruction(models.Model):
    _name = "shipping.instruction"
    _description = 'Shipping Instruction model details.'
    _order = "sequence"

    name = fields.Char('Name')
    sequence = fields.Integer(string="Sequence", default=0)
    active = fields.Boolean(string="Archived", default=True)


class PurchaseLineStatus(models.Model):
    _name = "purchase.line.status"
    _description = 'Purchase Order Line Status model details.'
    _order = "sequence"

    name = fields.Char('Name')
    sequence = fields.Integer(string="Sequence", default=0)
    active = fields.Boolean(string="Archived", default=True)


class PurchaseOrderLine(models.Model):
    _inherit = ['purchase.order.line', 'mail.thread', 'mail.activity.mixin']
    _name = 'purchase.order.line'

    def _default_po_line_status(self):
        draft_status_id = self.env.ref('bista_purchase.status_line_draft')
        return draft_status_id.id

    purchase_tracking_line_ids = fields.One2many(
        'purchase.tracking.line', 'po_line_id', string="Tracking Lines")
    status_id = fields.Many2one('po.status.line', string="Status", copy=False,
                                ondelete="restrict", tracking=True)
    tracking_ref = fields.Char(
        'Tracking Refrence', compute="get_tracking_ref")

    @api.depends('move_ids.state')
    def get_tracking_ref(self):
        """Get the tracking reference."""
        for line in self:
            tracking_ref = line.move_ids.filtered(
                lambda x: x.picking_type_id.code == 'incoming'
                          and x.quantity_done).mapped('picking_id').mapped('carrier_tracking_ref')
            tracking_ref = ', '.join([str(elem)
                                      for elem in tracking_ref if elem])
            line.tracking_ref = tracking_ref

    def open_po_line(self):
        self.ensure_one()
        return {
            'name': _('Purchase Order Line'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.line',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_id': self.id,
            'view_id': self.env.ref('bista_purchase.purchase_order_line_form').id,
            'context': {'create': False, 'edit': False},
            'flags': {'mode': 'readonly'},
        }

    def check_bo_transfer(self):
        name = ''
        picking_ids = self.env['stock.picking'].search([('picking_type_code', '=', 'incoming'),
                                                        ('partner_id', '=',
                                                         self.order_id.partner_id.id),
                                                        ('backorder_id',
                                                         '!=', False),
                                                        ('state', 'not in', ['done', 'cancel'])])
        pick_id = picking_ids.move_ids_without_package.filtered(
            lambda x: x.product_id == self.product_id)
        if pick_id:
            for ref in pick_id:
                name += '\n' + ref.picking_id.name
        return name

    @api.onchange('product_id')
    def onchange_product_vendor(self):
        result = {}
        bo_transfer = self.check_bo_transfer()
        if self.product_id and bo_transfer:
            message = _('"%s" Product is already in back order. you can check this backorder. %s') % (
                self.product_id.display_name, bo_transfer)

            warning_mess = {
                'title': _('WARNING!'),
                'message': message
            }
            result = {'warning': warning_mess}
        return result

    @api.constrains('product_id')
    def _check_exist_product_in_line(self):
        exist_product_list = []
        products_list = ''
        for line in self:
            if line.product_id.id in exist_product_list:
                product_ref = '' if not line.product_id.default_code else '[' + line.product_id.default_code + '] '
                products_list = products_list + '\n' + \
                                product_ref + \
                                line.product_id.name
            exist_product_list.append(line.product_id.id)
        duplicate_product_list = set([x for x in exist_product_list if exist_product_list.count(x) > 1])
        if duplicate_product_list and len(list(duplicate_product_list)) > 1:
            raise ValidationError(
                _(' Following products are already added in line, you can Update the qty there. ' + products_list))
        elif duplicate_product_list:
            raise ValidationError(
                _(products_list + ' is already added in line, you can Update the qty there.'))

    def action_purchase_history(self):
        ''' can show the purchase order line history in purchase order line. where user can see back order qty
        details '''
        if self.order_id.date_approve:
            domain = [('display_type', '=', False),
                      ('product_id', '=', self.product_id.id),
                      ('order_id.partner_id', '=', self.order_id.partner_id.id),
                      ('order_id.state', 'not in', ['draft', 'cancel'])]
            action = self.env.ref('bista_orders_report.''action_purchase_order_line_status').read()[0]
            action.update({'domain': domain})
            return action
        if self.order_id.date_order:
            domain = [('display_type', '=', False),
                      ('product_id', '=', self.product_id.id),
                      ('order_id.partner_id', '=', self.order_id.partner_id.id),
                      ('order_id.state', 'not in', ['done', 'cancel'])]
            action = self.env.ref('bista_orders_report.''action_purchase_order_line_status').read()[0]
            action.update({'domain': domain})
            return action


class PoStatus(models.Model):
    _name = "po.status.line"
    _description = "Status Line"
    _order = "sequence"

    name = fields.Char("Status Name", required=True)
    sequence = fields.Integer(string="Sequence", default=0)
    manual_update = fields.Boolean(default=True)
    active = fields.Boolean(string="Archived", default=True)
