# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
import logging
from datetime import datetime
from odoo import api, fields, models, tools, _
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.exceptions import UserError, ValidationError
import pprint
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
Error1 = _("Braintree Errors 1: Braintree Payment Gateway Currently not Configure for this Currency pls Connect Your Shop Provider !!!")
Error2 = _("Braintree Errors 2: Authentication Error: API keys are incorrect.")
Error3 = _("Braintree Errors 3: Authorization Error: not authorized to perform the attempted action.")
Error4 = _("Braintree Errors 4: Issue occure while generating clinet token, pls contact your shop provider.")
Error5 = _("Braintree Errors 5: Default 'Merchant Account ID' not found.")
Error6 = _("Braintree Errors 6: Transaction not Found.")
Error7 = _("Braintree Errors 7: Error occured while payment processing or Some required data missing.")
Error8 = _("Braintree Errors 8: Validation error occured. Please contact your administrator.")
Error9 = _("Braintree Errors 9: Payment has been recevied on braintree end but some error occured during processing the order.")
Error10 = _("Braintree Errors 10: Unknow Error occured. Unable to validate the Braintree payment.")
SuccessMsg = _("Payment Successfully recieved and submitted for settlement.")

_logger = logging.getLogger(__name__)


class TransactionBraintree(models.Model):
    _inherit = 'payment.transaction'

    brt_txnid = fields.Char('Transaction ID')
    brt_txcurrency = fields.Char('Transaction Currency')

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'braintree':
            return res
        acquirer = self.acquirer_id
        tx_values, message, token, merchant_account_id = dict(), None, None, None
        currency = self.currency_id.name
        merchant_account = acquirer._process_merchant_account_id(currency)
        if merchant_account['status']:
            merchant_account_id = merchant_account['merchant_account_id']
            token = acquirer._get_authorization_token(
                merchant_account_id).get("token")
        else:
            message = merchant_account.get('message')
        partner_first_name, partner_last_name = payment_utils.split_partner_name(
            self.partner_name)
        tx_values['enable_3d_secure'] = acquirer.enable_3d_secure if acquirer.authorization_process == 'client_token' else False
        tx_values['amount'] = round(self.amount, 2)
        tx_values['paypal_enabled'] = acquirer.brt_paypal_enabled
        tx_values['brt_version'] = acquirer.brt_version
        tx_values['currency'] = currency
        tx_values['reference'] = self.reference
        tx_values['billing_partner_email'] = self.partner_email
        tx_values['billing_partner_first_name'] = partner_first_name
        tx_values['billing_partner_last_name'] = partner_last_name
        tx_values['billing_partner_phone'] = self.partner_phone
        tx_values['billing_partner_address'] = self.partner_address
        tx_values['billing_partner_city'] = self.partner_city
        tx_values['billing_partner_state'] = self.partner_state_id.code
        tx_values['billing_partner_zip'] = self.partner_zip
        tx_values['billing_partner_country'] = self.partner_country_id.code
        tx_values['tx_url'] = acquirer._braintree_action_url()
        tx_values['display_currency'] = self.currency_id
        tx_values['token'] = token
        tx_values['merchant_account_id'] = merchant_account_id
        tx_values['message'] = message
        return tx_values

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'braintree':
            return tx
        
        reference, amount, currency, acquirer_reference = data.get('reference'), data.get(
            'amount'), data.get('currency'), data.get('acquirer_reference')
        if not data.get('token_save', False):
            if not reference or not amount or not currency or not acquirer_reference:
                raise ValidationError(
                    "2c2p: " + _(
                        "Received data with missing reference (%(ref)s) or acquirer_reference (%(aq_ref)s) or Amount (%(amount)s)",
                        ref=reference, aq_ref=acquirer_reference, amount=amount
                    )
                )
        tx = self.search([('reference', '=', reference),
                         ('provider', '=', provider)])
        if not tx:
            raise ValidationError(
                "2c2p: " +
                _("No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_feedback_data(self, data):
        super()._process_feedback_data(data)
        if self.provider != 'braintree':
            return

        status = data.get('status')
        res = {
            'brt_txnid': data.get('acquirer_reference'),
            'acquirer_reference': data.get('acquirer_reference'),
            'state_message': data.get('tx_msg'),
            'brt_txcurrency': data.get('currency'),
        }
        if self.tokenize:
            self._braintree_tokenize_from_feedback_data(data)
        if status:
            _logger.info(
                'Validated Braintree payment for tx %s: set as done' % (self.reference))
            self._set_done()
        self.write(res)

    def _braintree_tokenize_from_feedback_data(self, data):
        """ Create a new token based on the feedback data.

        :param dict data: The feedback data built with Braintree objects. See `_process_feedback_data`.
        :return: None
        """
        if data.get('vaulted') or data.get('token_save'):
            token = self.env['payment.token'].create({
                'acquirer_id': self.acquirer_id.id,
                'name': payment_utils.build_token_name(data.get('payment_method').last_4),
                'partner_id': self.partner_id.id,
                'acquirer_ref': data.get('customer_id'),
                'verified': True,
                'braintree_payment_method': data.get('payment_method').token,
            })
            self.write({
                'token_id': token,
                'tokenize': False,
            })
            if data.get('customer_id') and self.partner_id.braintree_cust_id != data['customer_id']:
                self.partner_id.braintree_cust_id = data['customer_id']
            _logger.info(
                "created token with id %s for partner with id %s", token.id, self.partner_id.id
            )
        else:
            _logger.info(
                "requested tokenization of non-vaulted payment method")
            return

    def _send_payment_request(self):
        """ Override of payment to send a payment request to braintree with a confirmed PaymentIntent.

        Note: self.ensure_one()

        :return: None
        :raise: UserError if the transaction is not linked to a token
        """
        super()._send_payment_request()
        values = {'status': False}
        if self.provider != 'braintree':
            return

        # Make the payment request to Braintree
        if not self.token_id:
            raise UserError(
                "Braintree: " + _("The transaction is not linked to a token."))
        try:
            response = self._braintree_create_payment_intent()
            if response['status']:
                response = response['response']
                if response.is_success:
                    values = {
                                'status': response.is_success,
                                'reference': self.reference,
                                'currency': response.transaction.currency_iso_code,
                                'amount': response.transaction.amount,
                                'acquirer_reference': response.transaction.id,
                                'partner_reference': response.transaction.customer.get('email'),
                                'tx_msg': SuccessMsg
                                }
                    _logger.info("entering _handle_feedback_data with data:\n%s",
                                pprint.pformat(values))
                    self._handle_feedback_data('braintree', values)
                else:
                    message = "Payment Failed: %s, %s" % (response.message, " ".join(error.message for error in response.errors.errors))
                    self.sudo()._set_error(message)
                    values['message'] = message
            else:
                values['message'] = response['message']
        except Exception as e:
            _logger.error("Braintree exception: %r", e)  # debug
            if values['status']:
                self.sudo().write({
                    'brt_txnid': values['acquirer_reference'],
                    'acquirer_reference':values['acquirer_reference'],
                    'state': 'error',
                    'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'state_message': Error9,
                })
                values['message'] = Error9
            elif not values['status']:
                self.sudo()._set_error(Error1)
                values['message'] = e or Error1
            else:
                values['message'] = Error10
                values.update({ 'status': False, 'redirect_brt': True, 'message': Error10 })
        return values
        

    def _braintree_create_payment_intent(self):
        """ Create and return a PaymentIntent.

        Note: self.ensure_one()

        :return: The Payment Intent
        :rtype: dict
        """
        response = self.acquirer_id._braintree_token_payment(
            payload=self._braintree_prepare_payment_intent_payload(),
        )
        return response

    def _braintree_prepare_payment_intent_payload(self):
        """ Prepare the payload for the creation of a payment intent in Braintree format.
        :return: The Braintree-formatted payload for the payment intent request
        :rtype: dict
        """
        return {
            'amount': str(self.amount),
            'customer_id': self.token_id.acquirer_ref,
            "options": {"submit_for_settlement": True},
            'payment_method_token': self.token_id.braintree_payment_method,
            'merchant_account_id': self.acquirer_id.brt_merchant_account_id,
            'order_id': self.reference,
        }
