# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    po_conf = fields.Text(string='PO Conf #')
    clock_start_override = fields.Date(string='Clock Starts Override')
    clock_override_reason = fields.Text(string='Clock Starts Override Reason')
    hours_process = fields.Char(string='Hours to Process')

    # Review Order Notes and Requirements
    order_notes = fields.Text(string='Order Notes')
    fulfilment_project = fields.Boolean(string="Fulfilment Project")
    ordered_by = fields.Many2one(related="sale_order_ids.partner_id", string="Ordered By")
    ops_project_owner_id = fields.Many2one('res.users', string='Ops Project Owner')
    payment_receive_date = fields.Date(string='Payment Received Date')
    billing_notes = fields.Text(string="Billing Notes")
    cc_email = fields.Char(string="CC Email")
    supplier_nuances = fields.Text(string="Supplier Nuances", related="partner_id.supplier_nuances")
    minimum_nuances = fields.Text(string="Minimums Nuances", related="partner_id.minimums_nuances")
    pre_approval_nuances = fields.Text(string="Pre Approval Nuances", related="partner_id.pre_approval_nuances")
    transfer_to_bookpal_warehouse = fields.Boolean(string="Transfer to BookPal Warehouse")
    type = fields.Selection([('customer', 'Customer'),
                             ('supplier', 'Supplier'),
                             ('credit', 'Credit'),
                             ], string="Type")
    supplier_warehouse = fields.Many2one('stock.warehouse', string='Supplier Warehouse')

    future_ship_nuances = fields.Text(string="Future Ship Nuances", related="partner_id.future_ship_nuances")
    shipping_nuances = fields.Text(string="Shipping Nuances", related="partner_id.shipping_nuances")
    processing_time_nuances = fields.Text(string="Processing Time Nuances",
                                          related="partner_id.processing_time_nuances")
    author_event_naunces = fields.Text(string="Author Event Nuances", related="partner_id.author_event_naunces")
    author_event_shipping_naunces = fields.Text(string="Author Event Shipping Nuances",
                                                related="partner_id.author_event_shipping_naunces")
    rush_status_id = fields.Many2one('rush.status', string='Rush Status')
    shipping_instructions = fields.Char(string='Shipping Instructions')
    order_shipping_desc = fields.Char(string='Order Shipping Description')
    default_supplier_shipping = fields.Char(string='Default Supplier Shipping')
    freight_charges = fields.Text(string='Freight Charges')
    rush_shipping_nuances = fields.Text(string="Rush Shipping Nuances", related="partner_id.rush_processing_nuances")
    shipping_acct_nuances = fields.Text(string="Shipping Acct Nuances", related="partner_id.shipping_acct_nuances")
    freight_nuances = fields.Text(string="Freight Nuances", related="partner_id.frieght_nuances")
    opening_text_nuances = fields.Text(string="Opening Text Nuances", related="partner_id.opening_text_nuances")
    note_to_vendor_nuances = fields.Text(string="Note to Vendor Nuances", related="partner_id.note_to_vendor_nuances")
    memo = fields.Text(string="Memo")
    supplier_order_number = fields.Char(string="Supplier Order Number")
    special_pick_note = fields.Html('Special Instructions and Notes')
    num_of_need_by_days = fields.Text(string='Num of Need By Days')
    sale_order_ids = fields.Many2many('sale.order', compute="compute_sale_order_ids")
    purchase_tracking_ids = fields.One2many('purchase.tracking', 'order_id', string="Purchase Tracking")


    def compute_sale_order_ids(self):
        for order_id in self:
            order_id.sale_order_ids = order_id._get_sale_orders()

    def compute_sale_order_ids(self):
        for order_id in self:
            order_id.sale_order_ids = order_id._get_sale_orders()

    def update_po_lines(self):
        po_lines = self.env['purchase.order.line'].search([('id', 'in', self.order_line.ids)])

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

    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({'note': self.special_pick_note})
        return res


class RushStatus(models.Model):
    _name = "rush.status"
    _description = 'Rush Status model details.'


class UpdateStatus(models.Model):
    _name = "update.status"

class PurchaseOrderLine(models.Model):
    _inherit = ['purchase.order.line', 'mail.thread', 'mail.activity.mixin']
    _name = 'purchase.order.line'

    status = fields.Selection([('draft', 'Draft'),
                               ('ready_for_preview', 'Ready For Preview '),
                               ('ordered', 'Ordered '),
                               ('pending', 'Pending/In Transint'),
                               ('received', 'Received'),
                               ('stocked', 'Stocked'),
                               ('completed', 'Completed'),
                               ('return_created', 'Return created'),
                               ('rush_ordered', 'Rush Ordered'),
                               ('on_hold', 'On Hold'),
                               ('canceled', 'Canceled'),
                               ('invoiced', 'Invoiced'),
                               ('partially_received', 'Partially Received')], default='draft', tracking=True)


    # def write(self, vals):
    #     res = super(PurchaseOrderLine, self).write(vals)
    #     print('self', self)
    #     for line in self:
    #         print('line', line.name, line.status, line.order_id)
    #         status_flag = True
    #         for all_poline in line.order_id.order_line:
    #             print("all order id", all_poline)
    #             if all_poline.status != 'ordered':
    #                 status_flag = False
    #         if status_flag:
    #             line.order_id.write({
    #                 'state': 'purchase'
    #             })
    #     return res

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

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line model details.'

    def check_bo_transfer(self):
        name = ''
        picking_ids = self.env['stock.picking'].search([('picking_type_code', '=', 'incoming'),
                                                        ('partner_id', '=', self.order_id.partner_id.id),
                                                        ('backorder_id', '!=', False),
                                                        ('state', 'not in', ['done', 'cancel'])])
        pick_id = picking_ids.move_ids_without_package.filtered(lambda x: x.product_id == self.product_id)
        if pick_id:
            for ref in pick_id:
                name += '\n' + ref.picking_id.name
        return name

    @api.onchange('product_id')
    def onchange_product_vendor(self):
        result = {}
        bo_transfer = self.check_bo_transfer()
        if self.product_id and bo_transfer:
            message = _('"%s" Product is already in back order. you can check this backorder. %s') \
                (self.product_id.display_name, bo_transfer)

            warning_mess = {
                'title': _('WARNING!'),
                'message': message
            }
            result = {'warning': warning_mess}
        return result
