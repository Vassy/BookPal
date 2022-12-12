import email
import email.policy
import logging
from xmlrpc import client as xmlrpclib

from odoo import _, api, exceptions, fields, models, tools, registry, SUPERUSER_ID

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def message_process(self, model, message, custom_values=None,
                        save_original=False, strip_attachments=False,
                        thread_id=None):
        if isinstance(message, xmlrpclib.Binary):
            message = bytes(message.data)
        if isinstance(message, str):
            message = message.encode('utf-8')
        message = email.message_from_bytes(message, policy=email.policy.SMTP)

        # parse the message, verify we are not in a loop by checking message_id is not duplicated
        msg_dict = self.message_parse(message, save_original=save_original)

        if strip_attachments:
            msg_dict.pop('attachments', None)

        re_read_mail_check = self.env['ir.config_parameter'].sudo().get_param(
            'bista_odoo_azure.re_read_mails')
        if re_read_mail_check:
            # parse the message, verify we are not in a loop by checking message_id is not duplicated
            existing_msg_ids = self.env['mail.message'].search([('message_id', '=', msg_dict['message_id'])], limit=1)
            existing_msg_ids.unlink()

        existing_msg_ids = self.env['mail.message'].search([('message_id', '=', msg_dict['message_id'])], limit=1)
        if existing_msg_ids:
            _logger.info('Ignored mail from %s to %s with Message-Id %s: found duplicated Message-Id during processing',
                         msg_dict.get('email_from'), msg_dict.get('to'), msg_dict.get('message_id'))
            return False
        # find possible routes for the message
        routes = self.message_route(message, msg_dict, model, thread_id, custom_values)
        thread_id = self._message_route_process(message, msg_dict, routes)
        return thread_id

    @api.model
    def message_parse(self, message, save_original=False):
        res = super(MailThread, self).message_parse(message, save_original)
        res['reply_to'] = tools.decode_message_header(message, 'Reply-To').strip()
        return res


class FetchmailServer(models.Model):
    _inherit = 'fetchmail.server'

    def fetch_mail(self):
        res = super(FetchmailServer, self).fetch_mail()
        self.env['ir.config_parameter'].set_param("bista_odoo_azure.re_read_mails", False)
        return res
