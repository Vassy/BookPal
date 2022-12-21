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
    journal_customization_ids = fields.Many2many(
        'journal.customization', string='Journal Customization')
    customization_cost = fields.Monetary('Our Customization Cost')
    link_to_art_files = fields.Text(string='Link to Art Files')
    artwork_status_id = fields.Many2one(
        'artwork.status', string='Artwork Status')
    journal_notes = fields.Text(string='Journal Notes')
    journal_setup_fee = fields.Monetary(string="Journal Set Up Fee")
    journal_setup_fee_waived = fields.Monetary(string="Journal Set Up Fee Waived")
    shipping_account = fields.Char(string="Shipping Account")
    shipping_cost = fields.Monetary(string=" Our Shipping Cost")
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
                                              string='Account Order Standing', store=True)
    # customer_email_add = fields.Char(
    #     'Customer Email Address', related='partner_id.email')
    saving_amount = fields.Monetary(
        "Total Saving Amount", compute="_amount_all", store=True
    )
    is_report = fields.Boolean(string='Report', default=True, tracking=True)
    reason = fields.Char(string='Reason')
    report_type = fields.Selection([
                    ('individual', 'Individual'),
                    ('bulk', 'Bulk'),
                    ('mixed', 'Mixed'),
                ], string='Report Type')
    report_notes = fields.Text(string='Reporting Notes')

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

    @api.constrains('journal_setup_fee', 'journal_setup_fee_waived', 'customization_cost', 'shipping_cost')
    def warning_journal_setup_fee(self):
        if self.journal_setup_fee < 0:
            raise ValidationError("journal setup fee waived  value is negative,add positive value.")
        if self.journal_setup_fee_waived < 0:
            raise ValidationError("journal setup fee waived value is  negative,add positive value.")
        if self.customization_cost < 0:
            raise ValidationError("customization cost value is negative,add positive value.")
        if self.shipping_cost < 0:
            raise ValidationError("shipping cost  value is negative,add positive value.")

    @api.onchange('fulfilment_project')
    def onchange_fulfilment_project(self):
        if self.fulfilment_project:
            self.report_type = 'individual'


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    tracking_ref = fields.Char(
        "Tracking Refrence", compute="get_tracking_ref"
    )
    saving_amount = fields.Float(
        "Saving Amount", compute="_compute_amount", store=True
    )
    discounted_price = fields.Float(
        "Discounted Unit Price", compute="_compute_amount", store=True
    )
    attachment_ids = fields.Many2many('ir.attachment', string="Attach File")

    @api.depends("product_uom_qty", "discount", "price_unit", "tax_id")
    def _compute_amount(self):
        super()._compute_amount()
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.currency_id:
                price = line.currency_id.round(price)
            taxes = line.tax_id.compute_all(
                price,
                line.order_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id
            )
            line_data = {
                "discounted_price": price,
                "saving_amount": price * line.product_uom_qty,
                "price_tax": sum(t.get("amount", 0.0) for t in taxes.get("taxes", [])),
                "price_total": taxes["total_included"],
                "price_subtotal": taxes["total_excluded"],
            }
            line.update(line_data)

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

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.product_id:
            vendor = self.product_id._prepare_sellers({}).filtered(
                lambda s: not s.company_id or s.company_id == self.company_id
            )[:1]
            if vendor:
                self.supplier_id = vendor.filtered(lambda x: x.name.is_primary).name.id if vendor.filtered(lambda x: x.name.is_primary) else vendor[:1].name.id
        return res
