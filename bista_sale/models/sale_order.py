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
    # shipping_account = fields.Char(string="Shipping Account")
    shipping_account = fields.Selection([
            ("our_account", "Our Account"),
            ("castelli_account", "Castelli's Account")]
            , string='Shipping Account')
    so_shipping_cost = fields.Monetary(string=" Our Shipping Cost")
    death_type_id = fields.Many2one('death.type', string='Die Type')
    existing_death_order = fields.Char(string="Existing Die Order #")
    # Shipping Info.
    shipping_notes = fields.Text(string='Shipping Notes')
    shipping_to = fields.Boolean('Shipping to Hotel or Event Venue')
    potential_pallets = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Potential Pallets')
    accept_pallets = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Accept Pallets')
    has_loading_dock = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Has Loading Dock')
    inside_delivery_req = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Inside Delivery Required')
    # Project & Fulfilment Tracking.
    fulfilment_project = fields.Boolean('Fulfillment Project')
    am_owner = fields.Char(string="AM Owner")
    project_description = fields.Char(string="Project Description")
    project_status = fields.Char(string="Project Status")
    status_notes = fields.Text(string='Status Notes')
    # delivery_location = fields.Char(string="Delivery Location")
    delivery_location = fields.Selection([
            ("domestic", "Domestic"),
            ("international", "International"),
            ("domestic_int", "Domestic/International")]
            ,string='Delivery Location')
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
    quote_processing_time = fields.Char(string='Quotation Process Days', default="0 Days")
    product_weight = fields.Float(compute="_compute_product_weight", string="Product Weight")
    weight_uom_name = fields.Char(string='Weight unit of measure label', compute="_compute_weight_uom")
    product_use = fields.Char(string='Product Use')
    # compurl = fields.Char(string="compute url", compute="compute_url")

    @api.depends("order_line.price_total")
    def _amount_all(self):
        super()._amount_all()
        for sale in self:
            sale.saving_amount = sum(sale.order_line.mapped("saving_amount"))

    @api.depends('picking_ids.is_dropship')
    def _compute_picking_ids(self):
        super()._compute_picking_ids()
        for order in self:
            order.delivery_count -= len(order.picking_ids.filtered(lambda p: p.sequence_code in ["IN", "INT"]))

    def action_view_delivery(self):
        return self._get_action_view_picking(
            self.picking_ids.filtered(lambda p: not p.is_dropship and p.sequence_code not in ["IN", "INT"])
        )

    @api.constrains('journal_setup_fee', 'journal_setup_fee_waived', 'customization_cost', 'so_shipping_cost')
    def warning_journal_setup_fee(self):
        if self.journal_setup_fee < 0:
            raise ValidationError("journal setup fee waived  value is negative,add positive value.")
        if self.journal_setup_fee_waived < 0:
            raise ValidationError("journal setup fee waived value is  negative,add positive value.")
        if self.customization_cost < 0:
            raise ValidationError("customization cost value is negative,add positive value.")
        if self.so_shipping_cost < 0:
            raise ValidationError("shipping cost  value is negative,add positive value.")

    @api.onchange('fulfilment_project')
    def onchange_fulfilment_project(self):
        if self.fulfilment_project:
            self.report_type = 'individual'

    # def compute_quote_process_time(self):
    #     for quote in self:
    #         print("quote_confirm", quote)
    #         print("quote_confirm", quote.state, quote.quote_processing_time)
    #         if quote.state in ('draft', 'quote_confirm'):
    #             print("\n\n\ninside----------")
    #             quote_process_time = 0
    #             print("date_order.date()", quote.date_order)
    #             print("date_order.date()", quote.create_date)
    #             if quote.date_approve:
    #                 quote_date = quote.date_approve.date() - quote.date_order.date()
    #                 quote_process_time = quote_date.days
    #             quote.quote_processing_time = str(quote_process_time)


    @api.depends('order_line.product_uom_qty', 'order_line.product_id')
    def _compute_product_weight(self):
        for order in self:
            final_weight = sum(line.product_id.weight * line.product_uom_qty for line in order.order_line.filtered(lambda l: l.product_id.type in ('product')))
        order.product_weight = final_weight

    def _compute_weight_uom(self):
        self.weight_uom_name = self.env['product.template']._get_weight_uom_name_from_ir_config_parameter()

    def action_open_delivery_wizard(self):
        res = super(SaleOrder, self).action_open_delivery_wizard()
        if self.opportunity_id.carrier_id.id:
            res['context'].update({
                'default_carrier_id': self.opportunity_id.carrier_id.id
            })
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    tracking_ref = fields.Char("Tracking Refrence", compute="get_tracking_ref")
    saving_amount = fields.Float("Saving Amount", compute="_compute_prices", store=True)
    discounted_price = fields.Float(
        "Quote Price",
        compute="_compute_prices",
        store=True,
        inverse="_inverse_discounted_price",
    )
    attachment_ids = fields.Many2many("ir.attachment", string="Attach File")

    def _inverse_discounted_price(self):
        for line in self:
            line.discount = 0
            if line.price_unit:
                line.discount = 100 - (line.discounted_price / line.price_unit * 100)
            line.saving_amount = (
                    line.price_unit * line.discount / 100 * line.product_uom_qty
            )
        self._compute_amount()

    @api.depends("product_uom_qty", "price_unit", "discount")
    def _compute_prices(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line_data = {
                "discounted_price": int(price * 10 ** 2) / 10 ** 2,
                "saving_amount": (line.price_unit - price) * line.product_uom_qty,
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
                self.supplier_id = vendor.filtered(lambda x: x.name.is_primary).name.id if vendor.filtered(
                    lambda x: x.name.is_primary) else vendor[:1].name.id
        return res

    @api.model
    def create(self, vals_list):
        """Fix attachment ownership"""
        rec = super(SaleOrderLine, self).create(vals_list)
        if rec.attachment_ids:
            rec.attachment_ids.write({'res_model': self._name, 'res_id': rec.id})
        return rec
