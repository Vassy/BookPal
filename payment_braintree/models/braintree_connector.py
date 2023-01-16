# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#################################################################################
from urllib import response
import braintree
import functools
import logging

from odoo import _

_logger = logging.getLogger(__name__)


class BraintreeConnector(object):

    def __init__(self, merchant_id, public_key ,private_key, environment='sandbox'):
        """__init__"""
        Environment = braintree.Environment.Production if environment=='production' else braintree.Environment.Sandbox
        self.gateway = braintree.BraintreeGateway(
            braintree.Configuration(
                Environment,
                merchant_id=merchant_id,
                public_key=public_key,
                private_key=private_key
            )
        )

    def braintree_exception(function):
        """
        A decorator that wraps the passed in function and return
        exceptions should one occurs
        """
        result = {'status': False, 'message': '', 'response': False}

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except braintree.exceptions.authentication_error.AuthenticationError as e:
                _logger.error("----------------------Braintree Exception=%r", e)
                result['message'] = 'AuthenticationError: API keys are incorrect'
            except braintree.exceptions.authorization_error.AuthorizationError as e:
                _logger.error("----------------------Braintree Exception=%r", e)
                result['message'] = 'AuthorizationError'
            except braintree.exceptions.invalid_challenge_error.InvalidChallengeError as e:
                _logger.error("----------------------Braintree Exception=%r", e)
                result['message'] = 'InvalidChallengeError'
            except braintree.exceptions.invalid_signature_error.InvalidSignatureError as e:
                _logger.error("----------------------Braintree Exception=%r", e)
                result['message'] = 'InvalidSignatureError'
            except braintree.exceptions.not_found_error.NotFoundError as e:
                _logger.error("----------------------Braintree Exception=%r", e)
                result['message'] = str(e)
            except braintree.exceptions.server_error.ServerError as e:
                _logger.error("----------------------Braintree Exception=%r", e)
                result['message'] = 'ServerError'
            except braintree.exceptions.unexpected_error.UnexpectedError as e:
                _logger.error("----------------------Braintree Exception=%r", e)
                result['message'] = 'UnexpectedError'
            except braintree.exceptions.too_many_requests_error.TooManyRequestsError as e:
                _logger.error("----------------------Braintree Exception=%r", e)
                result['message'] = 'TooManyRequestsError'
            except braintree.exceptions.upgrade_required_error.UpgradeRequiredError as e:
                _logger.error("----------------------Braintree Exception=%r", e)
                result['message'] = 'UpgradeRequiredError'
            except Exception as e:
                # Something else happened, completely unrelated to Braintree
                _logger.error("----------------------Braintree Exception=%r", e)
                result['message'] = 'Unknow exception occured.'
            return result
        return wrapper

    @braintree_exception
    def _get_client_token(self, merchant_account_id):
        """_get_client_token"""
        client_token = self.gateway.client_token.generate({
            'merchant_account_id': merchant_account_id
        })
        return {
            'status': True,
            'token': client_token
        }

    @braintree_exception
    def _fetch_merchant_account(self, merchant_account_id):
        """_fetch_merchant_account"""
        merchant_account = self.gateway.merchant_account.find(merchant_account_id)
        return {
            'status': True,
            'account_status': merchant_account.status,
            'account_currency': merchant_account.currency_iso_code
        }

    @braintree_exception
    def _create_transaction(self, vals):
        """_create_transaction"""
        response = self.gateway.transaction.sale(vals)
        return {
            'status': True,
            'response': response
        }
        
    @braintree_exception
    def _create_payment_method(self, vals):
        if vals.get('customer_id'):
            response = self.gateway.payment_method.create(vals)
        else:
            response = self.gateway.customer.create(vals)
        return {
            'status': True,
            'response': response
        }
    