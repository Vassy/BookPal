# -*- coding: utf-8 -*-
from odoo import  _,api,fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"


    common_pick_note = fields.Html('Common Notes')
    white_glove_id = fields.Many2one('white.glove.type', string='White Glove Type')
    event_date = fields.Date(string="Event Date")
    order_notes = fields.Text(string="Order Notes")
    product_status_notes = fields.Text(string="Product Status Notes")
    gorgias_ticket = fields.Text(string="Gorgias Ticket")
    ce_notes = fields.Text(string="CE Notes")
    payment_notes = fields.Text(string="Payment Notes")
    am_notes = fields.Text(string="AM Notes")
    ce_ops_acct_notes = fields.Text(string="CE-Ops Acct Notes")
    billing_notes = fields.Text(string="Billing Notes")
    placed_from_ip = fields.Char(string="Placed from IP")
    # journal or promotional product fields
    journal_customization_id = fields.Many2one('journal.customization', string='Journal Customization')
    customization_cost = fields.Float('Our Customization Cost')
    link_to_art_files = fields.Text(string='Link to Art Files')
    artwork_status_id = fields.Many2one('artwork.status', string='Artwork Status')
    journal_notes = fields.Text(string='Journal Notes')
    journal_setup_fee = fields.Char(string="Journal Set Up Fee")
    journal_setup_fee_waived = fields.Char(string="Journal Set Up Fee Waived")
    shipping_account = fields.Char(string="Shipping Account")
    shipping_cost = fields.Float(string="Shipping Cost")
    death_type_id = fields.Many2one('death.type', string='Death Type')
    existing_death_order = fields.Char(string="Existing Death Order #")
    # Project & Fulfilment Tracking.
    fulfilment_project = fields.Boolean('Fulfilment Project')
    am_owner = fields.Char(string="AM Owner")
    project_description = fields.Char(string="Project Description")
    project_status = fields.Char(string="Project Status")
    status_notes = fields.Text(string='Status Notes')
    delivery_location = fields.Char(string="Delivery Location")
    shipping_instruction = fields.Text(string='Shipping Instruction')
    customization_type_ids = fields.Many2many('customization.type', string="Customization Type")
    special_insert_note = fields.Text(string='Special Insert Notes')
    attachment_note = fields.Text(string='Attachment Notes')
    individual_mailer_return_receiver = fields.Char(string="Individual Mailer Return Receiver")
    recipient_list_status = fields.Char(string="Recipient List Status")
    recipient_list_expected = fields.Char(string="Recipient List Expected")
    individual_mailer_return_address = fields.Char(string="Individual Mailer Return Address")
    book_status = fields.Char(string="Book Status")
    on_hold_reason = fields.Text(string='On Hold Reason(s)')



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    picking_note = fields.Text('Picking Note')

    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        values.update({
            'picking_note': self.picking_note,
        })
        return values