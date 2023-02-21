# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2022 (https://www.bistasolutions.com)
#
##############################################################################

import binascii

from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.addons.sale.controllers.portal import PaymentPortal


class ModCustomerPortal(CustomerPortal):
    def _prepare_quotations_domain(self, partner):
        states = ["draft", "quote_approval", "quote_confirm", "sent", "cancel"]
        return [
            ("message_partner_ids", "child_of", [partner.commercial_partner_id.id]),
            ("state", "in", states),
        ]

    def _prepare_orders_domain(self, partner):
        return [
            ("message_partner_ids", "child_of", [partner.commercial_partner_id.id]),
            ("state", "in", ["order_booked", "pending_for_approval", "sale", "done"]),
        ]

    @http.route(
        ["/my/orders/<int:order_id>/accept"], type="json", auth="public", website=True
    )
    def portal_quote_accept(
        self, order_id, access_token=None, name=None, signature=None
    ):
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get("access_token")
        try:
            order_sudo = self._document_check_access(
                "sale.order", order_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return {"error": _("Invalid order.")}

        if not order_sudo.has_to_be_signed():
            msg = _("The order is not in a state requiring customer signature.")
            return {"error": msg}
        if not signature:
            return {"error": _("Signature is missing.")}

        try:
            data = {
                "signed_by": name,
                "signed_on": fields.Datetime.now(),
                "signature": signature,
            }
            order_sudo.write(data)
            request.env.cr.commit()
        except (TypeError, binascii.Error):
            return {"error": _("Invalid signature data.")}

        if not order_sudo.has_to_be_paid():
            order_sudo.action_order_booked()

        report_id = request.env.ref("sale.action_report_saleorder")
        pdf = report_id.with_user(SUPERUSER_ID)._render_qweb_pdf([order_sudo.id])[0]

        _message_post_helper(
            "sale.order",
            order_sudo.id,
            _("Order signed by %s") % (name,),
            attachments=[("%s.pdf" % order_sudo.name, pdf)],
            **({"token": access_token} if access_token else {})
        )

        query_string = "&message=sign_ok"
        if order_sudo.has_to_be_paid(True):
            query_string += "#allow_payment=yes"
        return {
            "force_refresh": True,
            "redirect_url": order_sudo.get_portal_url(query_string=query_string),
        }


class BistaPaymentPortal(PaymentPortal):
    def _create_transaction(
        self, *args, sale_order_id=None, custom_create_values=None, **kwargs
    ):
        response = super()._create_transaction(
            *args,
            sale_order_id=sale_order_id,
            custom_create_values=custom_create_values,
            **kwargs
        )
        if sale_order_id:
            request.env["sale.order"].browse(sale_order_id).action_order_booked()
        return response
