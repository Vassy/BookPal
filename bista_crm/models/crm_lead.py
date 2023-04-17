# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    google_search_team = fields.Text(string="Google Search Term")
    estim_deal_size = fields.Text(string="Estimated Deal Size")
    estim_deal_close_date = fields.Char(string="Estimated Deal Closed Date")

    # product fields
    pre_release = fields.Boolean(string="Pre-Release")
    product_use = fields.Text(string="Product Use")
    product_status_notes = fields.Text(string="Product Status Notes")
    special_pricing_type_id = fields.Many2one(
        "special.pricing.type", string="Special Pricing Type"
    )
    special_pricing_notes = fields.Text(string="Special Pricing Notes")

    # Billing Fields
    bigcommerce_customer_id = fields.Char(related="partner_id.bigcommerce_customer_id")
    tax_exempt_category = fields.Char(related="partner_id.tax_exempt_category")
    payment_notes = fields.Text(string="Payment Notes")

    # Shipping Info fields
    shipping_address = fields.Text(string="Shipping Address")
    carrier_id = fields.Many2one("delivery.carrier", string="Shipping Method")
    event_date = fields.Date(string="Event Date")
    need_date = fields.Date(string="Need By Date")
    international_shipping = fields.Char(string="International Shipping")
    order_notes = fields.Text(string="Order Notes")
    shipping_notes = fields.Text(string="Shipping Notes")
    shipping_to = fields.Boolean("Shipping to Hotel or Event Venue")
    potential_pallets = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Potential Pallets"
    )
    accept_pallets = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Accept Pallets"
    )
    has_loading_dock = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Has Loading Dock"
    )
    inside_delivery_req = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Inside Delivery Required"
    )

    # Journal Info fields
    journal_customization_ids = fields.Many2many(
        "journal.customization", string="Journal Customization"
    )
    customization_cost = fields.Monetary("Our Customization Cost")
    link_to_art_files = fields.Char(string="Link to Art Files")
    artwork_status_id = fields.Many2one("artwork.status", string="Artwork Status")
    journal_notes = fields.Text(string="Journal Notes")
    # journal_setup_fee = fields.Monetary(
    #     string="Journal Set Up Fee")
    journal_setup_fee = fields.Selection(
        [("waived", "Waived"), ("75", "$75.00")], string="Journal Set Up Fee"
    )

    death_type_id = fields.Many2one("death.type", string="Die Type")
    existing_death_order = fields.Text(string="Existing Die Order #")

    # Fulfillment Fields
    fulfilment_project = fields.Boolean("Fulfillment Project")
    customization_type_ids = fields.Many2many(
        "customization.type", string="Customization Type"
    )
    project_details = fields.Text(string="Project Details")

    shipping_instructions = fields.Text(string="Shipping Instructions")
    special_insert_note = fields.Text(string="Special Insert Notes")
    fulfilment_warehouse = fields.Many2one(
        "fulfillment.warehouse", string="FullFilment WareHouse"
    )
    order_shipping_type = fields.Selection(
        [
            ("international", "International"),
            ("domestic", "Domestic"),
            ("both", "Both"),
        ],
        string="International or Domestic",
    )
    ind_mailer_return_address = fields.Text(string="Ind Mailer Return Address")
    attachment_note = fields.Text(string="Attachment Notes")

    # deal Close Fields
    close_won_order_time = fields.Datetime("Close Won Order Time")
    deal_close_amount_override = fields.Char(string="Deal Close Amount Override")
    split_order_number = fields.Char(string="Number of Orders Split On")
    currency_id = fields.Many2one(
        "res.currency", string="Currency", related="company_id.currency_id"
    )
    referring_organization = fields.Many2one(
        "res.partner", string="Referring Organization"
    )
    referred = fields.Many2one("res.partner", string="Referred By")

    def action_new_quotation(self):
        res = super(CrmLead, self).action_new_quotation()
        new_context = {
            "default_link_to_art_files": self.link_to_art_files,
            "default_journal_notes": self.journal_notes,
            "default_journal_customization_ids": self.journal_customization_ids.ids,
            "default_customization_cost": self.customization_cost,
            "default_artwork_status_id": self.artwork_status_id.id,
            "default_journal_setup_fee": self.journal_setup_fee,
            "default_existing_death_order": self.existing_death_order,
            "default_death_type_id": self.death_type_id.id,
            "default_shipping_instruction": self.shipping_instructions,
            "default_customization_type_ids": self.customization_type_ids.ids,
            "default_fulfilment_project": self.fulfilment_project,
            "default_special_insert_note": self.special_insert_note,
            "default_individual_mailer_return_receiver": self.ind_mailer_return_address,
            "default_attachment_note": self.attachment_note,
            "default_commitment_date": self.need_date,
            "default_event_date": self.event_date,
            "default_order_notes": self.order_notes,
            "default_payment_notes": self.payment_notes,
            "default_product_status_notes": self.product_status_notes,
            "default_shipping_to": self.shipping_to,
            "default_potential_pallets": self.potential_pallets,
            "default_accept_pallets": self.accept_pallets,
            "default_has_loading_dock": self.has_loading_dock,
            "default_inside_delivery_req": self.inside_delivery_req,
            "default_shipping_notes": self.shipping_notes,
            "default_internal_note": self.description,
            "default_project_description": self.project_details,
            "default_refer_by_person": self.referred.id,
            "default_refer_by_company": self.referring_organization.id,
            "default_product_use": self.product_use,
            "no_change_refer": True,
        }
        res["context"].update(new_context)
        return res

    @api.onchange("partner_id")
    def onchange_shipping_method_partner_id_to_crm(self):
        """Onchange shipping method.
        Partner shipping method values automatically fetched
        in crm shipping method"""
        if self.partner_id:
            if self.partner_id.property_delivery_carrier_id:
                self.carrier_id = self.partner_id.property_delivery_carrier_id.id
            self.referred = self.partner_id.referal_source
            self.referring_organization = self.partner_id.referring_organization

    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        """Update carrier in partner from lead."""
        partner_data = {
            "property_delivery_carrier_id": self.carrier_id.id,
            "referal_source": self.referred.id,
            "referring_organization": self.referring_organization.id,
        }
        result = super()._prepare_customer_values(partner_name, is_company, parent_id)
        result.update(partner_data)
        return result


class SpecialPricingType(models.Model):
    _name = "special.pricing.type"
    _description = "Special Pricing Type"

    name = fields.Char("Name")


class FulfillmentWarehouse(models.Model):
    _name = "fulfillment.warehouse"
    _description = "fulfillment warehouse"

    name = fields.Char("Name")
