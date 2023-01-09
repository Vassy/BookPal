# -*- coding: utf-8 -*-

from odoo import models, api


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        result = super().message_post(**kwargs)
        if kwargs.get("email_cc"):
            for mail_id in result.mail_ids:
                if mail_id.email_cc:
                    mail_id.email_cc += "," + kwargs["email_cc"]
                else:
                    mail_id.email_cc = kwargs["email_cc"]
        return result
