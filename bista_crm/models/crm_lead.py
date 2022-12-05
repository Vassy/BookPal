# -*- coding: utf-8 -*-
from odoo import api, _, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    google_search_team = fields.Char(string='Google Search Term')
    estim_deal_size = fields.Char(string='Estimated Deal Size')
    estim_deal_close_date = fields.Char(string='Estimated Deal Closed Date')

    # product fields
    # deal_title = fields.Char(string="Deal Title")
    pre_release = fields.Boolean(string="Pre-Release")
    product_use = fields.Char(string='Product Use')
    product_status_notes = fields.Text(string='Product Status Notes')
    special_pricing_type_id = fields.Many2one('special.pricing.type', string='Special Pricing Type')
    special_pricing_notes = fields.Text(string='Special Pricing Notes')

    # Billing Fields
    billing_address = fields.Char(string='Billing Address')
    tax_exempt = fields.Selection([('yes', 'Yes'),
                                   ('no', 'No'),
                                   ], string="Tax Exempt")
    # payment_method = fields.Char(string='Payment Method')
    payment_notes = fields.Text(string='Payment Notes')

    # Shipping Info fields
    shipping_address = fields.Char(string='Shipping Address')
    carrier_id = fields.Many2one('delivery.carrier', string='Shipping Method')
    event_date = fields.Date(string="Event Date")
    need_date = fields.Date(string="Need By Date")
    international_shipping = fields.Char(string='International Shipping')
    order_notes = fields.Text(string='Order Notes')
    shipping_notes = fields.Text(string='Shipping Notes')
    shipping_to = fields.Boolean('Shipping to Hotel or Event Venue')
    potential_pallets = fields.Char(string='Potential Pallets')
    accept_pallets = fields.Char(string='Accept Pallets')
    has_loading_dock = fields.Char(string='Has Loading Dock')
    inside_delivery_req = fields.Char(string='Inside Delivery Required')

    # Journal Info fields
    journal_customization_id = fields.Many2many('journal.customization', string='Journal Customization')
    customization_cost = fields.Float('Our Customization Cost')
    link_to_art_files = fields.Char(string='Link to Art Files')
    artwork_status_id = fields.Many2one('artwork.status', string='Artwork Status')
    journal_notes = fields.Text(string='Journal Notes')
    journal_setup_fee = fields.Char(string="Journal Set Up Fee")
    death_type_id = fields.Many2one('death.type', string='Die Type')
    existing_death_order = fields.Char(string="Existing Die Order #")

    # Fulfillment Fields
    fulfilment_project = fields.Boolean('Fulfilment Project')
    customization_type_ids = fields.Many2many('customization.type', string="Customization Type")
    project_details = fields.Char(string="Project Details")

    shipping_instructions = fields.Char(string='Shipping Instructions')
    special_insert_note = fields.Text(string='Special Insert Notes')
    fulfilment_warehouse = fields.Many2one('fulfillment.warehouse', string='FullFilment WareHouse')
    order_shipping_type = fields.Selection([('international', 'International'),
                                            ('domestic', 'Domestic'),
                                            ('both', 'Both'),
                                            ], string="International or Domestic")
    ind_mailer_return_address = fields.Char(string="Ind Mailer Return Address")
    attachment_note = fields.Char(string="Attachment Notes")

    # deal Close Fields
    # close_won_order = fields.Char('Close Won Order #')
    close_won_order_time = fields.Datetime('Close Won Order Time')
    # actual_close_amount = fields.Datetime('Actual Close Amount')
    deal_close_amount_override = fields.Char(string='Deal Close Amount Override')
    # created_by = fields.Char(string='Created By')
    # deal_close_lost_date = fields.Date(string='Close Lost Date')
    # deal_close_lost_reason = fields.Char(string='Close Lost Reason')
    split_order_number = fields.Char(string='Number of Orders Split On')

    # sale_order_count = fields.Char(string="Orders Count", compute="compute_sale_order_ids")

    def action_new_quotation(self):
        res = super(CrmLead, self).action_new_quotation()
        res['context'].update({
            'default_link_to_art_files': self.link_to_art_files,
            'default_journal_notes': self.journal_notes,
            'default_journal_customization_id': self.journal_customization_id.ids,
            'default_customization_cost': self.customization_cost,
            'default_artwork_status_id': self.artwork_status_id.id,
            'default_journal_setup_fee': self.journal_setup_fee,
            'default_existing_death_order': self.existing_death_order,
            'default_death_type_id': self.death_type_id.id,
            'default_shipping_instruction': self.shipping_instructions,
            'default_customization_type_ids': self.customization_type_ids.ids,
            'default_fulfilment_project': self.fulfilment_project,
            'default_special_insert_note': self.special_insert_note,
            'default_individual_mailer_return_receiver': self.ind_mailer_return_address,
            'default_attachment_note': self.attachment_note,

        })

        return res


class SpecialPricingType(models.Model):
    _name = "special.pricing.type"
    _description = 'Special Pricing Type'

    name = fields.Char('Name')


class FulfillmentWarehouse(models.Model):
    _name = "fulfillment.warehouse"
    _description = 'fulfillment warehouse'

    name = fields.Char('Name')
