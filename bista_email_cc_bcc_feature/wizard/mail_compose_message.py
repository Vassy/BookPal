# -*- encoding: utf-8 -*-

import base64
import psycopg2
import smtplib
import re
import logging

from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo import _, api, fields, models, tools
from odoo.tools.safe_eval import safe_eval
from ast import literal_eval

_logger = logging.getLogger(__name__)


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    @api.model
    def default_get(self, fields):
        res = super(MailComposeMessage, self).default_get(fields)
        cc_check = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mail_compose_message.enable_cc")
        )
        bcc_check = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mail_compose_message.enable_bcc")
        )
        res.update(
            {
                "enable_cc": cc_check,
                "enable_bcc": bcc_check,
            }
        )
        if cc_check:
            vals = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("mail_compose_message.cc_recipient_ids")
            )
            cc_recipient_ids = literal_eval(vals)
            if res.get("cc_recipient_ids"):
                cc_recipient_ids.extend(res["cc_recipient_ids"])
            res.update(
                {
                    "cc_recipient_ids": cc_recipient_ids,
                }
            )
        if bcc_check:
            vals = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("mail_compose_message.bcc_recipient_ids")
            )
            if self._context.get('from_purchase_trackig', False):
                bcc_partner = self.env["res.partner"].search([
                    ('name', '=', 'support@bookpal.com'),
                    ('email', '=', 'support@bookpal.com')], limit=1)
                vals = str([bcc_partner.id])
            if self._context.get('active_model') == 'sale.order':
                vals = str(False)
            res.update(
                {
                    "bcc_recipient_ids": literal_eval(vals)
                }
            )
        return res

    cc_recipient_ids = fields.Many2many(
        "res.partner", "cc_field_tag_rel", "partner_id", "cc_id", string="Cc"
    )
    bcc_recipient_ids = fields.Many2many(
        "res.partner", "bcc_field_tag_rel", "part_id", "bcc_id", string="Bcc"
    )
    enable_cc = fields.Boolean(string="Enable CC")
    enable_bcc = fields.Boolean(string="Enable BCC")

    def get_mail_values(self, res_ids):
        """Generate the values that will be used by send_mail to create mail_messages
        or mail_mails."""
        self.ensure_one()
        results = super(MailComposeMessage, self).get_mail_values(res_ids)
        for res_id in res_ids:
            # static wizard (mail.message) values
            results[res_id].update(
                {
                    "cc_recipient_ids": self.cc_recipient_ids,
                    "bcc_recipient_ids": self.bcc_recipient_ids,
                }
            )
        return results


class Message(models.Model):
    """Messages model: system notification (replacing res.log notifications),
    comments (OpenChatter discussion) and incoming emails."""

    _inherit = "mail.message"

    cc_recipient_ids = fields.Many2many(
        "res.partner",
        "mail_message_res_partner_cc_rel",
        "message_id",
        "partner_id",
        string="Cc (Partners)",
    )
    bcc_recipient_ids = fields.Many2many(
        "res.partner",
        "mail_message_res_partner_bcc_rel",
        "message_id",
        "partner_id",
        string="Bcc (Partners)",
    )

    def message_format(self):
        res = super(Message, self).message_format()
        for obj in res:
            cc_partners = ""
            bcc_partners = ""
            cc_partners_list = (
                self.env["res.partner"]
                .browse(obj.get("cc_recipient_ids", []))
                .read(["name", "country_id"])
            )
            for item in cc_partners_list:
                cc_partners += item.get("name") + ", "
            bcc_partners_list = (
                self.env["res.partner"]
                .browse(obj.get("bcc_recipient_ids", []))
                .read(["name"])
            )
            for item in bcc_partners_list:
                bcc_partners += item.get("name") + ", "
            obj["cc_partners"] = cc_partners
            obj["bcc_partners"] = bcc_partners
        return res

    def _get_message_format_fields(self):
        message_values = super(Message, self)._get_message_format_fields()
        return message_values + ["cc_recipient_ids", "bcc_recipient_ids"]


class Mail(models.Model):
    _inherit = "mail.mail"

    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None):
        IrMailServer = self.env["ir.mail_server"]
        IrAttachment = self.env["ir.attachment"]
        for mail_id in self.ids:
            success_pids = []
            failure_type = None
            processing_pid = None
            mail = None
            try:
                mail = self.browse(mail_id)
                if mail.state != "outgoing":
                    if mail.state != "exception" and mail.auto_delete:
                        mail.sudo().unlink()
                    continue

                # remove attachments if user send the link with the access_token
                body = mail.body_html or ""
                attachments = mail.attachment_ids
                for link in re.findall(r"/web/(?:content|image)/([0-9]+)", body):
                    attachments = attachments - IrAttachment.browse(int(link))

                # load attachment binary data with a separate read(), as prefetching all
                # `datas` (binary field) could bloat the browse cache, triggerring
                # soft/hard mem limits with temporary data.
                attachments = [
                    (a["name"], base64.b64decode(a["datas"]), a["mimetype"])
                    for a in attachments.sudo().read(["name", "datas", "mimetype"])
                ]

                # specific behavior to customize the send email for notified partners
                email_list = []
                cc_list = []
                bcc_list = []
                if mail.email_to:
                    email_list.append(mail._send_prepare_values())
                for partner in mail.recipient_ids:
                    values = mail._send_prepare_values(partner=partner)
                    values["partner_id"] = partner
                    email_list.append(values)
                for partner in mail.cc_recipient_ids:
                    cc_list += mail._send_prepare_values(partner=partner).get(
                        "email_to"
                    )
                for partner in mail.bcc_recipient_ids:
                    bcc_list += mail._send_prepare_values(partner=partner).get(
                        "email_to"
                    )
                # headers
                headers = {}
                ICP = self.env["ir.config_parameter"].sudo()
                bounce_alias = ICP.get_param("mail.bounce.alias")
                catchall_domain = ICP.get_param("mail.catchall.domain")
                if bounce_alias and catchall_domain:
                    if mail.mail_message_id.is_thread_message():
                        headers["Return-Path"] = "%s+%d-%s-%d@%s" % (
                            bounce_alias,
                            mail.id,
                            mail.model,
                            mail.res_id,
                            catchall_domain,
                        )
                    else:
                        headers["Return-Path"] = "%s+%d@%s" % (
                            bounce_alias,
                            mail.id,
                            catchall_domain,
                        )
                if mail.headers:
                    try:
                        headers.update(safe_eval(mail.headers))
                    except Exception:
                        pass

                # Writing on the mail object may fail (e.g. lock on user) which
                # would trigger a rollback *after* actually sending the email.
                # To avoid sending twice the same email, provoke the failure earlier
                failure_reason = _(
                    "Error without exception. Probably due do sending an email without"
                    " computed recipients."
                )
                mail.write({"state": "exception", "failure_reason": failure_reason})
                # Update notification in a transient exception state to avoid concurrent
                # update in case an email bounces while sending all emails related to
                # current mail record.
                notifs = self.env["mail.notification"].search(
                    [
                        ("notification_type", "=", "email"),
                        ("mail_mail_id", "in", mail.ids),
                        ("notification_status", "not in", ("sent", "canceled")),
                    ]
                )
                if notifs:
                    notif_msg = _(
                        "Error without exception. Probably due do concurrent access "
                        "update of notification records. Please see with an "
                        "administrator."
                    )
                    notifs.sudo().write(
                        {
                            "notification_status": "exception",
                            "failure_type": "unknown",
                            "failure_reason": notif_msg,
                        }
                    )
                    # `test_mail_bounce_during_send`, force immediate update to obtain
                    # the lock. see rev. 56596e5240ef920df14d99087451ce6f06ac6d36
                    notifs.flush(
                        fnames=[
                            "notification_status",
                            "failure_type",
                            "failure_reason",
                        ],
                        records=notifs,
                    )

                # build an RFC2822 email.message.Message object and send it without
                # queuing
                res = None
                for email in email_list:
                    msg = IrMailServer.build_email(
                        email_from=mail.email_from,
                        email_to=email.get("email_to"),
                        subject=mail.subject,
                        body=email.get("body"),
                        body_alternative=email.get("body_alternative"),
                        email_cc=tools.email_split(mail.email_cc) + cc_list,
                        email_bcc=bcc_list,
                        reply_to=mail.reply_to,
                        attachments=attachments,
                        message_id=mail.message_id,
                        references=mail.references,
                        object_id=mail.res_id and ("%s-%s" % (mail.res_id, mail.model)),
                        subtype="html",
                        subtype_alternative="plain",
                        headers=headers,
                    )

                    processing_pid = email.pop("partner_id", None)
                    try:
                        res = IrMailServer.send_email(
                            msg,
                            mail_server_id=mail.mail_server_id.id,
                            smtp_session=smtp_session,
                        )
                        if processing_pid:
                            success_pids.append(processing_pid)
                        processing_pid = None
                    except AssertionError as error:
                        if str(error) == IrMailServer.NO_VALID_RECIPIENT:
                            failure_type = "mail_email_invalid"
                            # No valid recipient found for this particular
                            # mail item -> ignore error to avoid blocking
                            # delivery to next recipients, if any. If this is
                            # the only recipient, the mail will show as failed.
                            _logger.info(
                                "Ignoring invalid recipients for mail.mail %s: %s",
                                mail.message_id,
                                email.get("email_to"),
                            )
                        else:
                            raise
                if res:  # mail has been sent at least once, no major exception occured
                    mail.write(
                        {"state": "sent", "message_id": res, "failure_reason": False}
                    )
                    _logger.info(
                        "Mail with ID %r and Message-Id %r successfully sent",
                        mail.id,
                        mail.message_id,
                    )
                    # /!\ can't use mail.state here, as mail.refresh() will cause an error
                    # see revid:odo@openerp.com-20120622152536-42b2s28lvdv3odyr in 6.1
                mail._postprocess_sent_message(
                    success_pids=success_pids, failure_type=failure_type
                )
            except MemoryError:
                # prevent catching transient MemoryErrors, bubble up to notify user or
                # abort cron job instead of marking the mail as failed
                _logger.exception(
                    "MemoryError while processing mail with ID %r and Msg-Id %r. "
                    "Consider raising the --limit-memory-hard startup option",
                    mail.id,
                    mail.message_id,
                )
                # mail status will stay on ongoing since transaction will be rollback
                raise
            except (psycopg2.Error, smtplib.SMTPServerDisconnected):
                # If an error with the database or SMTP session occurs, chances are that
                # the cursor or SMTP session are unusable, causing further errors when
                # trying to save the state.
                _logger.exception(
                    "Exception while processing mail with ID %r and Msg-Id %r.",
                    mail.id,
                    mail.message_id,
                )
                raise
            except Exception as e:
                failure_reason = tools.ustr(e)
                _logger.exception(
                    "failed sending mail (id: %s) due to %s", mail.id, failure_reason
                )
                mail.write({"state": "exception", "failure_reason": failure_reason})
                mail._postprocess_sent_message(
                    success_pids=success_pids,
                    failure_reason=failure_reason,
                    failure_type="UNKNOWN",
                )
                if raise_exception:
                    if isinstance(e, (AssertionError, UnicodeEncodeError)):
                        if isinstance(e, UnicodeEncodeError):
                            value = "Invalid text: %s" % e.object
                        else:
                            # get the args of the original error, wrap into a value and
                            # throw a MailDeliveryException that is an except_orm, with
                            # name and value as arguments
                            value = ". ".join(e.args)
                        raise MailDeliveryException(_("Mail Delivery Failed"), value)
                    raise

            if auto_commit is True:
                self._cr.commit()
        return True
