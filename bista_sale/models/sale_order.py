# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    white_glove_id = fields.Many2one(
        'white.glove.type', string='White Glove Type')
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
    journal_customization_id = fields.Many2many(
        'journal.customization', string='Journal Customization')
    customization_cost = fields.Float('Our Customization Cost')
    link_to_art_files = fields.Text(string='Link to Art Files')
    artwork_status_id = fields.Many2one(
        'artwork.status', string='Artwork Status')
    journal_notes = fields.Text(string='Journal Notes')
    journal_setup_fee = fields.Float(string="Journal Set Up Fee")
    journal_setup_fee_waived = fields.Float(string="Journal Set Up Fee Waived")
    shipping_account = fields.Char(string="Shipping Account")
    shipping_cost = fields.Float(string=" Our Shipping Cost")
    death_type_id = fields.Many2one('death.type', string='Die Type')
    existing_death_order = fields.Char(string="Existing Die Order #")
    # Project & Fulfilment Tracking.
    fulfilment_project = fields.Boolean('Fulfilment Project')
    am_owner = fields.Char(string="AM Owner")
    project_description = fields.Char(string="Project Description")
    project_status = fields.Char(string="Project Status")
    status_notes = fields.Text(string='Status Notes')
    delivery_location = fields.Char(string="Delivery Location")
    shipping_instruction = fields.Text(string='Shipping Instruction')
    customization_type_ids = fields.Many2many(
        'customization.type', string="Customization Type")
    special_insert_note = fields.Text(string='Special Insert Notes')
    attachment_note = fields.Text(string='Attachment Notes')
    individual_mailer_return_receiver = fields.Char(
        string="Individual Mailer Return Receiver")
    recipient_list_status = fields.Char(string="Recipient List Status")
    recipient_list_expected = fields.Char(string="Recipient List Expected")
    individual_mailer_return_address = fields.Char(
        string="Individual Mailer Return Address")
    book_status = fields.Char(string="Book Status")
    on_hold_reason = fields.Text(string='On Hold Reason(s)')
    due_amount = fields.Monetary('Due Amount', related='partner_id.total_due')

    refer_by_company = fields.Char('Referring Organization')
    refer_by_person = fields.Char('Referring Person')
    account_order_standing = fields.Selection(related="partner_id.account_order_standing",
                                              string='Account Order Standing')
    customer_email_add = fields.Char('Customer Email Address', related='partner_id.email')
    saving_amount = fields.Monetary(
        "Total Saving Amount", compute="_amount_all", store=True
    )

    @api.depends("order_line.price_total")
    def _amount_all(self):
        super()._amount_all()
        for sale in self:
            sale.saving_amount = sum(sale.order_line.mapped("saving_amount"))

    @api.depends('picking_ids.is_dropship')
    def _compute_picking_ids(self):
        super()._compute_picking_ids()
        for order in self:
            order.delivery_count = len(order.picking_ids.filtered(lambda p: p.picking_type_id.code in ['outgoing',
                                                                                                       'internal'] and p.picking_type_id.sequence_code != 'INT'))

    def action_view_delivery(self):
        return self._get_action_view_picking(self.picking_ids.filtered(
            lambda p: not p.is_dropship and p.picking_type_id.code in ['outgoing',
                                                                       'internal'] and p.picking_type_id.sequence_code != 'INT'))


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    tracking_ref = fields.Char(
        "Tracking Refrence", compute="get_tracking_ref"
    )
    saving_amount = fields.Float(
        "Saving Amount", compute="_compute_amount", store=True
    )
    discounted_price = fields.Float(
        "Discounted Price", compute="_compute_amount", store=True
    )
    attachment_ids = fields.Many2many('ir.attachment', string="Attach File")

    @api.depends("product_uom_qty", "discount", "price_unit", "tax_id")
    def _compute_amount(self):
        super()._compute_amount()
        for line in self:
            saving_unit = (line.price_unit * line.discount) / 100
            line.saving_amount = saving_unit * line.product_uom_qty
            line.discounted_price = line.price_unit - saving_unit

    @api.depends("move_ids.state")
    def get_tracking_ref(self):
        """Get the tracking reference."""
        for line in self:
            tracking_ref = line.move_ids.filtered(
                lambda x: x.picking_type_id.code in
                          ['outgoing', 'incoming'] and
                          x.quantity_done).mapped(
                'picking_id').mapped('carrier_tracking_ref')
            tracking_ref = ', '.join([str(elem)
                                      for elem in tracking_ref if elem])
            line.tracking_ref = tracking_ref
