# -*- coding: utf-8 -*-

from odoo import models, fields


class MailComposer(models.TransientModel):
    _inherit = "mail.compose.message"

    cc_partner_ids = fields.Many2many(
        "res.partner", "mail_compose_message_cc_partner_rel", "wizard_id", "partner_id"
    )

    def get_mail_values(self, res_ids):
        results = super().get_mail_values(res_ids)
        for res_id in res_ids:
            email_cc = []
            if results[res_id].get("email_cc"):
                email_cc = [results[res_id]["email_cc"]]
            email_cc.extend(self.cc_partner_ids.mapped("email"))
            if email_cc:
                results[res_id].update({"email_cc": ",".join(email_cc)})
        return results
