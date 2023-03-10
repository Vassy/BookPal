
import logging
import poplib
import email
import email.policy

from xmlrpc import client as xmlrpclib

from odoo import fields, models, tools


_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 50
MAIL_TIMEOUT = 60

# Workaround for Python 2.7.8 bug https://bugs.python.org/issue23906
poplib._MAXLINE = 65536


class FetchmailServer(models.Model):
    _inherit = 'fetchmail.server'

    def fetch_mail(self):
        """Skip specific emails."""
        additionnal_context = {
            'fetchmail_cron_running': True
        }
        mail_therad = self.env['mail.thread']
        for server in self:
            _logger.info('start checking for new emails on %s server %s', server.server_type, server.name)
            additionnal_context['default_fetchmail_server_id'] = server.id
            count, failed = 0, 0
            imap_server = None
            pop_server = None
            if server.server_type == 'imap':
                try:
                    imap_server = server.connect()
                    imap_server.select()
                    result, data = imap_server.search(None, '(UNSEEN)')
                    for num in data[0].split():
                        res_id = None
                        result, data = imap_server.fetch(num, '(RFC822)')
                        imap_server.store(num, '-FLAGS', '\\Seen')
                        message = data[0][1]
                        if isinstance(message, xmlrpclib.Binary):
                            message = bytes(message.data)
                        if isinstance(message, str):
                            message = message.encode('utf-8')
                        message = email.message_from_bytes(message, policy=email.policy.SMTP)
                        email_from = tools.decode_message_header(
                            message, 'From', separator=',')
                        email_from_list = email_from.split('<')
                        email_from = email_from_list[1][:-1] if email_from_list else email_from
                        do_not_fetch_email = self.env['ir.config_parameter'].\
                            get_param('do_not_fetch_email', False)
                        if do_not_fetch_email:
                            do_not_fetch_email = do_not_fetch_email.split(',')
                            if email_from in do_not_fetch_email:
                                continue
                        try:
                            res_id = mail_therad.with_context(**additionnal_context).message_process(server.object_id.model, data[0][1], save_original=server.original, strip_attachments=(not server.attach))
                        except Exception:
                            _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                            failed += 1
                        imap_server.store(num, '+FLAGS', '\\Seen')
                        self._cr.commit()
                        count += 1
                    _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", count, server.server_type, server.name, (count - failed), failed)
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if imap_server:
                        imap_server.close()
                        imap_server.logout()
            elif server.server_type == 'pop':
                try:
                    while True:
                        failed_in_loop = 0
                        num = 0
                        pop_server = server.connect()
                        (num_messages, total_size) = pop_server.stat()
                        pop_server.list()
                        for num in range(1, min(MAX_POP_MESSAGES, num_messages) + 1):
                            (header, messages, octets) = pop_server.retr(num)
                            message = (b'\n').join(messages)
                            res_id = None
                            message = email.message_from_bytes(message, policy=email.policy.SMTP)
                            email_from = tools.decode_message_header(
                                message, 'From', separator=',')
                            email_from_list = email_from.split('<')
                            email_from = email_from_list[1][:-1] if email_from_list else email_from
                            do_not_fetch_email = self.env['ir.config_parameter'].\
                                get_param('do_not_fetch_email', False)
                            if do_not_fetch_email:
                                do_not_fetch_email = do_not_fetch_email.split(',')
                                if email_from in do_not_fetch_email:
                                    continue
                            try:
                                res_id = mail_therad.with_context(**additionnal_context).message_process(server.object_id.model, message, save_original=server.original, strip_attachments=(not server.attach))
                                pop_server.dele(num)
                            except Exception:
                                _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                                failed += 1
                                failed_in_loop += 1
                            self.env.cr.commit()
                        _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", num, server.server_type, server.name, (num - failed_in_loop), failed_in_loop)
                        # Stop if (1) no more message left or (2) all messages have failed
                        if num_messages < MAX_POP_MESSAGES or failed_in_loop == num:
                            break
                        pop_server.quit()
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if pop_server:
                        pop_server.quit()
            server.write({'date': fields.Datetime.now()})
        return True
