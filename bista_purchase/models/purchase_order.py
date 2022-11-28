# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    po_conf = fields.Text(string='PO Conf #')
    clock_start_override = fields.Date(string='Clock Starts Override')
    clock_override_reason = fields.Text(string='Clock Starts Override Reason')
    hours_process = fields.Char(string='Hours to Process')

    # Review Order Notes and Requirements
    order_notes = fields.Text(string='Order Notes')
    fulfilment_project = fields.Boolean(string="Fulfilment Project")
    ordered_by = fields.Many2one(
        related="sale_order_ids.partner_id", string="Ordered By")
    ops_project_owner_id = fields.Many2one(
        'res.users', string='Ops Project Owner')
    payment_receive_date = fields.Date(string='Payment Received Date')
    billing_notes = fields.Text(string="Billing Notes")
    cc_email = fields.Char(string="CC Email")
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
    shipping_instructions = fields.Char(string='Shipping Instructions')
    order_shipping_desc = fields.Char(string='Order Shipping Description')
    default_supplier_shipping = fields.Char(string='Default Supplier Shipping')
    freight_charges = fields.Text(string='Freight Charges')
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
    order_process_time = fields.Integer(compute="compute_order_process_time", string="Order Processing Time")

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
        return res

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

    @api.onchange('partner_id')
    def onchange_partner_id_cc_email(self):
        self.cc_email = self.partner_id.cc_email

        # def _prepare_picking(self):
        #     res = super(PurchaseOrder, self)._prepare_picking()
        #     res.update({'note': self.special_pick_note})
        #     return res

    @api.constrains('order_line')
    def _check_exist_product_in_line(self, vals=False):
        for purchase in self:
            exist_product_list = []
            products_in_lines = [product.id for product in purchase.mapped('order_line.product_id')]
            for line in purchase.order_line:
                if not vals:
                    if line.product_id.id in exist_product_list:
                        raise ValidationError(_('Product is already Existing.'))
                else:
                    if vals.id in products_in_lines:
                        raise ValidationError(_('Product is already Existing.'))
                exist_product_list.append(line.product_id.id)

    def compute_lead_time(self):
        for rec in self:
            rec.lead_time = 0
            if rec.date_approve:
                rec.lead_time = False
                date_list = rec.picking_ids.mapped('scheduled_date')
                date_list.sort(reverse=True)
                date_time = date_list[0].date() - rec.date_approve.date()
                rec.lead_time = date_time.days

    def compute_order_process_time(self):
        for rec in self:
            rec.order_process_time = 0
            if rec.sale_order_ids.split_shipment and rec.date_approve:
                rec.order_process_time = False
                vals = min(rec.sale_order_ids.sale_multi_ship_qty_lines.mapped('confirm_date'))
                if vals:
                    rec_date = rec.date_approve - vals
                    rec.order_process_time = rec_date.days
            else:
                if rec.sale_order_ids.date_order and rec.date_approve:
                    order_date = rec.date_approve - rec.sale_order_ids.date_order
                    rec.order_process_time = order_date.days


class RushStatus(models.Model):
    _name = "rush.status"
    _description = 'Rush Status model details.'


class PurchaseOrderLine(models.Model):
    _inherit = ['purchase.order.line', 'mail.thread', 'mail.activity.mixin']
    _name = 'purchase.order.line'

    def _default_po_line_status(self):
        draft_status_id = self.env.ref('bista_purchase.status_line_draft')
        return draft_status_id.id

    purchase_tracking_line_ids = fields.One2many('purchase.tracking.line', 'po_line_id', string="Tracking Lines")
    status_id = fields.Many2one('po.status.line', string="Status", default=_default_po_line_status, copy=False,
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

    @api.onchange('product_id')
    def onchange_product_is_exist(self):
        product_order = self.order_id._origin._check_exist_product_in_line(self.product_id)
        if self.product_id and product_order:
            return product_order


class PoStatus(models.Model):
    _name = "po.status.line"
    _description = "Status Line"
    _order = "sequence"

    name = fields.Char("Status Name", required=True)
    sequence = fields.Integer(string="Sequence", default=0)
    manual_update = fields.Boolean(default=True)
    active = fields.Boolean(string="Archived", default=True)
