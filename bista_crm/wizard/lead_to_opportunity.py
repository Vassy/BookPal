# -*- coding: utf-8 -*-

from odoo import models


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = "crm.lead2opportunity.partner"

    def _action_merge(self):
        lead_id = super()._action_merge()
        lead_data = {}
        if not lead_id.referring_organization:
            lead_data.update(
                {"referring_organization": lead_id.partner_id.referring_organization.id}
            )
        if not lead_id.referred:
            lead_data.update({"referred": lead_id.partner_id.referal_source.id})
        if lead_data:
            lead_id.write(lead_data)
        return lead_id
