# -*- coding: utf-8 -*-

from lxml import etree

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from odoo.tools import is_html_empty
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


AddState = [
    ("draft", "Purchase Order"),
    ("sent", "Order Sent"),
    ("to approve", "To Approve"),
    ("reject", "Rejected"),
    ("purchase", "Approved Order"),
    ("done", "Locked"),
    ("cancel", "Cancelled")
]


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # po_name = fields.Char(string="Purchase Order Name", related="name")
    po_conf = fields.Text(string='PO Conf #')
    clock_start_override = fields.Date(string='Clock Starts Override')
    clock_override_reason = fields.Text(string='Clock Starts Override Reason')
    hours_process = fields.Char(string='Hours to Process')

    # Review Order Notes and Requirements
    status = fields.Many2one('purchase.line.status', string='Purchase Order Line Status')
    order_notes = fields.Text(string='Order Notes')
    fulfilment_project = fields.Boolean(string="Fulfillment Project")
    ordered_by = fields.Many2one(
        related="order_line.partner_id", string="Ordered By")
    ops_project_owner_id = fields.Many2one(
        'res.users', string='Ops Project Owner')
    supplier_nuances = fields.Text(
        string="Supplier Nuances", related="partner_id.supplier_nuances")
    minimum_nuances = fields.Text(
        string="Minimums Nuances", related="partner_id.minimums_nuances")
    pre_approval_nuances = fields.Text(
        related="partner_id.pre_approval_nuances"
    )
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
    rush_status_id = fields.Many2one("rush.status", string="Shipping Method")
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
    rush = fields.Boolean(string="Rush")
    need_by_date = fields.Datetime(string="SO Need By Date", compute="_compute_need_by_date")
    date_planned = fields.Datetime(string="MAB Date")
    invoice_status = fields.Selection(selection_add=[('partial', 'Partially Billed')])

    @api.depends('state', 'order_line.qty_to_invoice', 'order_line.qty_to_invoice', 'order_line.qty_received')
    def _get_invoiced(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for order in self:
            if order.state not in ('purchase', 'done'):
                order.invoice_status = 'no'
                continue
            if any(
                not float_is_zero(line.qty_to_invoice, precision_digits=precision)
                for line in order.order_line.filtered(lambda l: not l.display_type)
            ) and not order.invoice_ids:
                order.invoice_status = 'to invoice'
            elif all(line.qty_invoiced == line.qty_received and line.qty_received > 0 and line.qty_invoiced > 0
                    for line in order.order_line.filtered(
                        lambda l: not l.display_type)) and order.invoice_ids:
                order.invoice_status = 'invoiced'
            elif any((line.qty_invoiced < line.qty_received
                     for line in order.order_line.filtered(lambda l: not l.display_type))) and order.invoice_ids:
                order.invoice_status = 'partial'
            else:
                order.invoice_status = 'no'

    def _compute_need_by_date(self):
        for purchase in self:
            if purchase.sale_order_ids:
                purchase.need_by_date = purchase.sale_order_ids.commitment_date
            else:
                purchase.need_by_date = False

    def default_get(self, fields):
        defaults = super().default_get(fields)
        po_terms = self.env["ir.config_parameter"].sudo().get_param(
            "bista_purchase.use_po_terms"
        )
        defaults["notes"] = po_terms and self.env.company.po_terms or ""
        return defaults

    def action_rfq_send(self):
        if not self.shipping_instructions and is_html_empty(self.special_pick_note):
            raise ValidationError(_('Please select the Shipping Instructions of Steps and Nuances tab and add the Notes'))
        if not self.shipping_instructions:
            raise ValidationError(_('Please select the Shipping Instructions of Steps and Nuances tab.'))
        if is_html_empty(self.special_pick_note):
            raise ValidationError(_('Please add the Notes'))
        result = super().action_rfq_send()
        cc_partner_ids = self.partner_id.child_ids.filtered(lambda p: p.is_primary)
        glove_id = self.sale_order_ids.mapped("white_glove_id")
        if glove_id:
            cc_partner_ids |= self.partner_id.child_ids.filtered(
                lambda p: glove_id in p.glove_type_ids
            )
        result["context"].update({"default_cc_recipient_ids": cc_partner_ids.ids})
        template_id = self.env["ir.model.data"]._xmlid_lookup(
            "bista_purchase.email_template_bista_purchase"
        )[2]
        if result.get("context") and result["context"].get("default_template_id"):
            result["context"]["default_template_id"] = template_id
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
        if not self.shipping_instructions and is_html_empty(self.special_pick_note):
            raise ValidationError(_('Please select the Shipping Instructions of Steps and Nuances tab and add the Notes'))
        if not self.shipping_instructions:
            raise ValidationError(_('Please select the Shipping Instructions of Steps and Nuances tab.'))
        if is_html_empty(self.special_pick_note):
            raise ValidationError(_('Please add the Notes'))
        return super(PurchaseOrder, self).button_approve()

    def button_confirm(self):
        # change order line status on confirm order
        res = super(PurchaseOrder, self).button_confirm()
        if not self.user_id:
            self.user_id = self.env.user.id
        ready_status_id = self.env.ref('bista_purchase.status_line_ready')
        if ready_status_id:
            for order in self:
                if not order._approval_allowed():
                    order.order_line.write({'status_id': ready_status_id.id})
        if not self.shipping_instructions and is_html_empty(self.special_pick_note):
            raise ValidationError(_('Please select the Shipping Instructions of Steps and Nuances tab and add the Notes'))
        if not self.shipping_instructions:
            raise ValidationError(_('Please select the Shipping Instructions of Steps and Nuances tab.'))
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

    def _prepare_supplier_info(self, partner, line, price, currency):
        # Changed vendor price from bp price to cover price
        res = super()._prepare_supplier_info(partner, line, price, currency)
        if line.before_disc_price_unit:
            res.update({'price': line.before_disc_price_unit})
        return res

    # @api.onchange('partner_id')
    # def onchange_partner_id_cc_email(self):
    #     self.cc_email = self.partner_id.cc_email

    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        # res.update({'note': self.special_pick_note})
        res.update({'user_id': self.env.user.id})
        return res

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
            max_date = sorted(rec.picking_ids.mapped("scheduled_date"), reverse=True)
            if rec.date_approve and max_date:
                rec.lead_time = (max_date[0].date() - rec.date_approve.date()).days

    def compute_order_process_time(self):
        for rec in self:
            process_time = 0
            ship_ids = rec.sale_order_ids.sale_multi_ship_qty_lines
            if rec.sale_order_ids.split_shipment and rec.date_approve and ship_ids:
                confirm_ids = ship_ids.filtered(lambda m: m.confirm_date)
                if confirm_ids:
                    min_date = min(confirm_ids.mapped("confirm_date"))
                    process_time = (rec.date_approve.date() - min_date.date()).days
            elif rec.sale_order_ids.date_order and rec.date_approve:
                process_time = (
                    rec.date_approve.date() - rec.sale_order_ids.date_order.date()
                ).days
            rec.order_process_time = process_time

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
        attrs = "{'readonly': [('state', 'in', ('purchase', 'done'))]}"
        if not self.env.user.has_group("purchase.group_purchase_manager"):
            attrs = "{'readonly': [('state', 'not in', ['draft', 'sent'])]}"
        else:
            for node in doc.xpath("//button[@id='draft_confirm']"):
                node.set('invisible', "1")
        for field in doc.xpath("//field"):
            if (
                field.attrib.get("invisible") == "1"
                or field.attrib.get("readonly") == "1"
                or field.attrib["name"] not in self._fields
                or field.attrib.get("attrs")
                or self._fields.get(field.attrib["name"]).readonly
                or field.attrib["name"] == "po_conf"
            ):
                continue
            field.attrib["attrs"] = attrs
        result["arch"] = etree.tostring(doc)
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Create Purchase Order Approval History """
        rec = super(PurchaseOrder, self).create(vals_list)
        white_glove = self.env['white.glove.type'].search([
            ('code', '=', 'AA')])
        if rec.origin:
            so_ids = [so_rec for so in rec.origin.split(',') if (so_rec := self.env['sale.order'].search([('name', '=', so)]))]
            flag = any(so_id.white_glove_id == white_glove for so_id in so_ids)
            rec.order_notes = '\n'.join(so_id.order_notes for so_id in so_ids if so_id.order_notes)
            rec.name += " " + "-" + " " + "AA" if flag else ""
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

    @api.constrains("date_approve", "date_planned")
    def warning_on_reciept_date(self):
        for record in self:
            if record.date_approve and record.date_planned:
                if record.date_planned.date() < record.date_approve.date():
                    raise ValidationError(
                        _("The Receipt date cannot be older than the confirmation date.")
                    )


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

    def _prepare_purchase_order_line_from_procurement(
        self, product_id, product_qty, product_uom, company_id, values, po
    ):
        result = super()._prepare_purchase_order_line_from_procurement(
            product_id, product_qty, product_uom, company_id, values, po
        )
        result["date_planned"] = values.get("date_planned") - relativedelta(days=1)
        return result

    def _default_po_line_status(self):
        draft_status_id = self.env.ref('bista_purchase.status_line_draft')
        return draft_status_id.id

    purchase_tracking_line_ids = fields.One2many(
        'purchase.tracking.line', 'po_line_id', string="Tracking Lines")
    status_id = fields.Many2one(
        "po.status.line", string="Line Status", copy=False, ondelete="restrict", tracking=True
    )
    tracking_ref = fields.Char(
        'Tracking Refrence', compute="get_tracking_ref")
    price_unit = fields.Float("BP Price")
    next_followup_date = fields.Date("Next Followup Date", copy=False)
    note = fields.Text("Notes", copy=False)
    po_line_status_log_ids = fields.One2many("po.status.line.log", "po_line_id")

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

    def go_back(self):
        context = self._context
        return {
            'name': 'Update PO Line Status',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'update.shipment.tracking',
            'view_id': self.env.ref("bista_purchase.update_shipment_tracking_form_view").id,
            'context': {'current_id': self.id, 'active_model': 'purchase.order', 'active_id': self.order_id.id},
            'target': 'new',
            'nodestroy': True,
        }


    def check_bo_transfer(self):
        name = ''
        picking_ids = self.env['stock.picking'].search([('picking_type_code', '=', 'incoming'),
                                                        ('partner_id', '=', self.order_id.partner_id.id),
                                                        ('product_id','=',self.order_id.product_id.id),
                                                        # ('backorder_id',
                                                        #  '!=', False),
                                                        ('state', 'in', ['assigned','confirmed'])])
        pick_id = picking_ids.move_ids_without_package.filtered(
            lambda x: x.product_id == self.product_id)
        if pick_id:
            for ref in pick_id:
                name += '\n' + ref.picking_id.name
        return name

    # As Discussed in 17820
    # @api.onchange('product_id')
    # def onchange_product_vendor(self):
    #     result = {}
    #     bo_transfer = self.check_bo_transfer()
    #     if self.product_id and bo_transfer:
    #         message = _('"%s" Product is already in back order. you can check this backorder. %s') % (
    #             self.product_id.display_name, bo_transfer)

    #         warning_mess = {
    #             'title': _('WARNING!'),
    #             'message': message
    #         }
    #         result = {'warning': warning_mess}
    #     return result

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
        ''' can show the purchase order line history in purchase order line.
        where user can see back order qty details '''
        domain = [
            ("product_id", "=", self.product_id.id),
            ("order_id.partner_id", "=", self.order_id.partner_id.id),
            ("line_status", "not in", ("received", "short_close")),
            ("state", "in", ("purchase", "done")),
        ]
        order_line = self.env["purchase.order.line"].search(domain)
        action = self.env.ref(
            "bista_orders_report.action_purchase_order_line_status"
        ).read()[0]
        action.update({"domain": [("id", "in", order_line.ids)]})
        return action


class PoStatus(models.Model):
    _name = "po.status.line"
    _description = "Status Line"
    _order = "sequence"

    name = fields.Char("Status Name", required=True)
    sequence = fields.Integer(string="Sequence", default=0)
    manual_update = fields.Boolean(default=True)
    active = fields.Boolean(string="Archived", default=True)
