# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
import logging
import pprint
from datetime import datetime
import werkzeug

from odoo.tools.translate import _
from odoo import http
from odoo.http import request
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

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
TokenSuccessMsg = _("Payment Token has been saved successfully.")

def _get_company(partner):
    if partner.company_type == 'company':
        return partner.name
    elif partner.parent_id.company_type == 'company':
        return partner.parent_id.name
    elif partner.company_id:
        return partner.company_id.name
    return partner.name

def _get_region(partner):
    if partner.country_id.code == 'US':
        return partner.state_id.code
    return partner.state_id.name

def _get_street(partner):
    street = partner.street
    if partner.street2:
        street = "%s, %s" %(street, partner.street2)
    return street


class BraintreeController(http.Controller):
    def get_transaction_vals(self, form_vals, order=None, tx=None):
        transaction_vals_dict, name = {}, False
        nonce_from_the_client = form_vals.get('payment_method_nonce')
        merchant_account_id = form_vals.get('merchant_account_id')
        if nonce_from_the_client and merchant_account_id:
            if tx.invoice_ids:
                invoice = tx.invoice_ids[0]
                customer_obj = partner_billing_obj = partner_shipping_obj = invoice.partner_id
                if invoice.partner_shipping_id:
                    partner_shipping_obj = invoice.partner_shipping_id
                name = invoice.name
            else:
                if tx and tx.partner_id and tx.operation == 'validation' and tx.tokenize:
                    customer_obj = tx.partner_id
                    transaction_vals_dict = {
                            "payment_method_nonce": nonce_from_the_client,
                        }
                    if customer_obj.braintree_cust_id:
                        transaction_vals_dict.update({
                            'customer_id': customer_obj.braintree_cust_id
                        })
                    else:
                        transaction_vals_dict.update({
                            "first_name": customer_obj.name,
                            "company": _get_company(customer_obj),
                            "email": customer_obj.email,
                            "phone": customer_obj.phone,
                        })
                    return transaction_vals_dict
                customer_obj = order.partner_id
                partner_billing_obj = order.partner_invoice_id
                partner_shipping_obj = order.partner_shipping_id
                name = order.name

            transaction_vals_dict = {
                    "amount":  form_vals.get('amount'),
                    "options": {"submit_for_settlement": True},
                    "order_id":  name,
                    "payment_method_nonce": nonce_from_the_client,
                    "merchant_account_id": merchant_account_id,
                    "customer": {
                        "first_name": customer_obj.name,
                        "company": _get_company(customer_obj),
                        "email": customer_obj.email,
                        "phone": customer_obj.phone,
                    },
                    "billing": {
                        "first_name": partner_billing_obj.name,
                        "company": _get_company(partner_billing_obj),
                        "street_address": _get_street(partner_billing_obj),
                        "locality": partner_billing_obj.city,
                        "region": _get_region(partner_billing_obj),
                        "postal_code": partner_billing_obj.zip,
                        "country_name": partner_billing_obj.country_id.name,
                        "country_code_alpha2": partner_billing_obj.country_id.code
                    },
                    "shipping": {
                        "first_name": partner_shipping_obj.name,
                        "street_address": _get_street(partner_shipping_obj),
                        "locality": partner_shipping_obj.city,
                        "region": _get_region(partner_shipping_obj),
                        "postal_code": partner_shipping_obj.zip,
                        "country_name": partner_shipping_obj.country_id.name,
                        "country_code_alpha2": partner_shipping_obj.country_id.code
                    }
                }
        return transaction_vals_dict

    def braintree_do_payment(self, **post):
        values, order = {'status': False}, None
        paymentTransaction = request.env['payment.transaction']
        transaction = paymentTransaction.sudo().search([('reference', '=', post.get('reference'))])
        if not transaction:
            values['message'] = Error6
            return values
        if not (transaction.invoice_ids or transaction.sale_order_ids):
            name = post.get('reference').split('-')[0]
            if name:
                invoices = request.env['account.move'].sudo().search([('name', '=', name)])
                if invoices:
                    transaction.sudo().write({
                        'invoice_ids': [(6, 0, invoices.ids)],
                        'partner_id': invoices[0].partner_id.id
                    })
        if hasattr(request, 'website') and hasattr(request.website, 'sale_get_order'):
            order = request.website.sale_get_order()
        if not order and transaction.sale_order_ids:
            order = transaction.sale_order_ids[0]

        transactionValues = self.get_transaction_vals(post, order, transaction)
        _logger.info('Braintree Api call with values %s', pprint.pformat(transactionValues))  # debug

        try:
            if transaction.operation == 'validation' and transaction.tokenize:
                response = transaction.acquirer_id._create_braintree_token(transactionValues)
            else:
                response = transaction.acquirer_id._create_braintree_transaction(transactionValues)
            if response['status'] and not transaction.operation == 'validation':
                response = response['response']
                if response.is_success:
                    values.update({
                        'status': response.is_success,
                        'reference': post.get('reference'),
                        'currency': response.transaction.currency_iso_code,
                        'amount': response.transaction.amount,
                        'acquirer_reference': response.transaction.id,
                        'partner_reference': response.transaction.customer.get('email'),
                        'tx_msg': SuccessMsg
                    })
                    if transaction.tokenize and response.transaction.vault_customer:
                        values.update({
                            'vaulted': True,
                            'customer_id': response.transaction.vault_customer.id,
                            'payment_method': response.transaction.vault_customer.payment_methods[0]
                        })
                    _logger.info('Braintree feedback_data with values %s', pprint.pformat(values))  # debug
                    paymentTransaction.sudo()._handle_feedback_data('braintree', values)
                else:
                    message = "Payment Failed: %s, %s" % (response.message, " ".join(error.message for error in response.errors.errors))
                    transaction.sudo()._set_error(message)
                    values['message'] = message
            elif response['status'] and transaction.operation == 'validation':
                response = response['response']
                if response.is_success:
                    if transaction.partner_id.braintree_cust_id:
                        values.update({
                            'status': response.is_success,
                            'reference': post.get('reference'),
                            'tx_msg': TokenSuccessMsg,
                            'currency': transaction.currency_id.name,
                            'acquirer_reference': response.payment_method.customer_id,
                            'amount': transaction.amount,
                            'token_save': True,
                            'customer_id': response.payment_method.customer_id,
                            'payment_method': response.payment_method
                        })
                    else:
                        values.update({
                            'status': response.is_success,
                            'reference': post.get('reference'),
                            'tx_msg': TokenSuccessMsg,
                            'currency': transaction.currency_id.name,
                            'acquirer_reference': response.customer.id,
                            'amount': transaction.amount,
                            'token_save': True,
                            'customer_id': response.customer.id,
                            'payment_method': response.customer.payment_methods[0]
                        })
                    _logger.info('Braintree feedback_data with values %s', pprint.pformat(values))  # debug
                    paymentTransaction.sudo()._handle_feedback_data('braintree', values)
                else:
                    message = "Payment Token Not Saved: %s, %s" % (response.message, " ".join(error.message for error in response.errors.errors))
                    transaction.sudo()._set_error(message)
                    values['message'] = message
            else:
                values['message'] = response['message']
        except Exception as e:
            _logger.error("Braintree exception: %r", e)  # debug

            if values['status']:
                transaction.sudo().write({
                    'brt_txnid': values['acquirer_reference'],
                    'acquirer_reference':values['acquirer_reference'],
                    'state': 'error',
                    'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'state_message': Error9,
                })
                values['message'] = Error9
            elif not values['status']:
                transaction.sudo()._set_error(Error1)
                values['message'] = e or Error1
            else:
                values['message'] = Error10
                values.update({ 'status': False, 'redirect_brt': True, 'message': Error10 })
        return values

    @http.route('/payment/braintree', type='http', auth="public", website=True, csrf=False)
    def braintree_payment(self, **post):
        """ Braintree Payment Controller """
        _logger.info('Beginning Braintree with post data %s', pprint.pformat(post))  # debug
        result = self.braintree_do_payment(**post)
        if not result['status']:
            return request.render("payment_braintree.barintree_error", {'error_message': result['message']})
        if result.get('token_save', False):
            return request.redirect('/my/payment_method')
        return request.redirect('/payment/status')
