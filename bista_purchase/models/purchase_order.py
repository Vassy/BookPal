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
    gorgias_ticket = fields.Text(string="Gorgias Ticket")
    supplier_order_number = fields.Char(string="Supplier Order Number")
    special_pick_note = fields.Html('Special Instructions and Notes')

    @api.onchange('partner_id')
    def onchange_partner_id_cc_email(self):
        self.cc_email = self.partner_id.cc_email

    def _prepare_picking(self):
        res = super(PurchaseOrder , self)._prepare_picking()
        res.update({'note': self.special_pick_note})
        return res


class RushStatus(models.Model):
    _name = "rush.status"
    _description = 'Rush Status model details.'

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line model details.'

    def check_bo_transfer(self):
        name = ''
        picking_ids = self.env['stock.picking'].search([('picking_type_code', '=', 'incoming'),\
            ('partner_id', '=', self.order_id.partner_id.id),\
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
            message = _('"%s" Product is already in back order. you can check this backorder. %s')\
                 %(self.product_id.display_name, bo_transfer)
            warning_mess = {
                'title': _('WARNING!'),
                'message': message
            }
            result = {'warning': warning_mess}
            return result
