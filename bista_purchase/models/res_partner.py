# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    type = fields.Selection(selection_add=[
                            ('return', 'Return Address'),
                            ('warehouse', 'Warehouse Address'),]
                            )
    is_primary = fields.Boolean(string="Primary Contact")

    # Supplier Details
    customer_service_email = fields.Char(string="Customer Service Email")
    customer_service_hours = fields.Char(string="Customer Service Hours")
    customer_service_phone = fields.Char(string="Customer Service Phone")
    rep = fields.Char(string="Rep")
    reviewed_date = fields.Date(string="Reviewed Date")
    account_number = fields.Char(string="Account Number")
    top_publisher = fields.Boolean(string="Top publisher")
    availability_check = fields.Char(string="Availability Check")

    # Nuances
    supplier_nuances = fields.Text(string="Supplier Nuances")
    shipping_acct_nuances = fields.Text(string="Shipping Acct Nuances")
    transfer_nuances = fields.Text(string="Transfer Nuances")
    future_ship_nuances = fields.Text(string="Future Ship Nuances")
    minimums_nuances = fields.Text(string="Minimums Nuances")
    shipping_nuances = fields.Text(string="Shipping Nuances")
    rush_processing_nuances = fields.Text(string="Rush Shipping Nuances")
    frieght_nuances = fields.Text(string="Freight Nuances")
    pre_approval_nuances = fields.Text(string="Pre Approval Nuances")
    processing_time_nuances = fields.Text(string="Processing Time Nuances")
    opening_text_nuances = fields.Text(string="Opening Text Nuances")
    note_to_vendor_nuances = fields.Text(string="Note to Vendor Nuances")
    author_event_naunces = fields.Text(string="Author Event Nuances")
    author_event_shipping_naunces = fields.Text(string="Author Event Shipping Nuances")
    publisher_nuances = fields.Text(string="Publisher Nuances")

    # Ops Processing
    cc_email = fields.Char(string="CC Email")

    # Finance
    invoice_issues_contact = fields.Char(string="Invoice Issues Contact")

    # Shipping Info
    dropship_applicable = fields.Boolean(string="Dropship")
    transfer_to_bp_warehouse = fields.Boolean(string="Transfer to BookPal Warehouse")
    # warehouse_zip_code = fields.Char(string="Warehouse Zip Code")
    # warehouse_address = fields.Char(string="Warehouse Address")
    default_shipping_id = fields.Many2one('delivery.carrier', "Default Shipping")
    non_conus_shipping = fields.Char(string="Non-CONUS Shipping")
    avg_processing_time = fields.Char(string="Days to ship")
    rush_processing_time = fields.Char(string="Rush days to ship")
    default_frieght_charges = fields.Float(string="Default Freight Charge")
    # return_address = fields.Char(string="Returns Address")
    shipping_notes = fields.Text(string="Shipping Notes")
    intl_shipping_notes = fields.Char(string="Int'l Shipping Notes")
    tracking_souurce = fields.Char(string="Tracking Source")

    # Discount Info
    avg_discount = fields.Float(string="Average Discount %")
    discount_notes = fields.Char(string="Discount Notes")
    minimums = fields.Boolean(string="Minimums")
    combine = fields.Boolean(string="Combine")
    pricing_profile = fields.Char(string="Pricing Profile")
    pricing_profile_notes = fields.Text(string="Pricing Profile Notes")
    price_match_discounts = fields.Char(string="Price Match Discounts")
    returnable_terms = fields.Text(string="Returnable Terms")
    # supplier_contact = fields.Char(string="Supplier Contact")
    supplier_discount = fields.Char(string="Supplier Discount (%)")

    product_count = fields.Integer(compute="_compute_product_count")
    product_tmpl_ids = fields.Many2many('product.template', compute="_compute_product_count")

    partner_shipping_ids = fields.One2many('res.partner.shipping', 'partner_id', string="Partner Shippings")

    def _compute_product_count(self):
        for partner_id in self:
            product_tmpl_ids = self.env['product.supplierinfo'].search([('name','=',partner_id.id)]).mapped('product_tmpl_id')
            partner_id.product_count = len(product_tmpl_ids)
            partner_id.product_tmpl_ids = product_tmpl_ids

    def open_partner_products(self):
        action = self.env['ir.actions.act_window']._for_xml_id('product.product_template_action_all')
        action['domain'] = [('id', 'in', self.product_tmpl_ids.ids)]
        return action

    def name_get(self):
        if self._context.get('res_partner_search_mode') != 'supplier':
            return super(ResPartner, self).name_get()
        res = []
        for partner in self:
            name = partner._get_name()
            if partner.is_primary:
                name += '  *'
            res.append((partner.id, name))
        return res

    @api.onchange('type')
    def _onchange_contact_type(self):
        if self.type != 'contact':
            self.is_primary = False

class ResPartnerShipping(models.Model):
    _name = 'res.partner.shipping'

    partner_id = fields.Many2one('res.partner', string="Vendor")
    # delivery_carrier_id = fields.Many2one('delivery.carrier', string="Delivery Carrier")
    # charge_type = fields.Selection([('free', "Free"),('paid',"Paid")], string="Charges Type")
    shipping_information = fields.Char(string="Shipping Information")
    amount = fields.Float(string="Charges")
    remarks = fields.Text(string="Remarks")
