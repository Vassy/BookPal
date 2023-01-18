# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
import logging

from ..models.braintree_connector import BraintreeConnector
from odoo import api, fields, models, tools, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_braintree.const import supported_currencies

_logger = logging.getLogger(__name__)


class BraintreeMerchantAccount(models.Model):
    _name = 'braintree.merchant.account'
    _description='Braintree Merchant Account'
    _rec_name='braintree_merchant_id'

    braintree_merchant_id = fields.Char(string="Merchant Account ID", required=True)
    braintree_merchant_currency = fields.Many2one('res.currency', string="Currency", required=True)
    braintree_merchant_validate = fields.Boolean(string="Is Valideted ?")
    currency_ref = fields.Many2one('payment.acquirer', string="ref key with table", invisible=True)

    _sql_constraints = [
        ('braintree_merchant_currency_uniq', 'unique(braintree_merchant_currency,id)', 'Merchant account id already present!'),
    ]

    def merchant_id_validate(self):
        for rec in self:
            resp = rec.currency_ref._validate_merchant_account_id(
                currency=rec.braintree_merchant_currency.name,
                merchant_account_id=rec.braintree_merchant_id,
                debug=True
            )
            if not resp['status']:
                raise ValidationError(resp['message'])
            rec.braintree_merchant_validate = True


    def merchant_id_un_validate(self):
        for rec in self:
            rec.braintree_merchant_validate = False

class AcquirerBraintree(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('braintree', 'Braintree')], ondelete={'braintree': 'set default'})
    brt_merchant_id = fields.Char('Merchant ID ', required_if_provider='braintree', groups='base.group_user')
    brt_public_key = fields.Char('Public Key', required_if_provider='braintree', groups='base.group_user')
    brt_private_key = fields.Char('Private Key', required_if_provider='braintree', groups='base.group_user')
    brt_merchant_account_id = fields.Char(string='Default Merchant Account ID', groups='base.group_user')
    enable_3d_secure = fields.Boolean(string="Enable 3D Secure", groups='base.group_user')
    brt_multicurrency = fields.Boolean(string="Multi-Currency Setup", groups='base.group_user')
    multicurrency_ids = fields.One2many('braintree.merchant.account', 'currency_ref', string="Merchant Account IDs")
    brt_tokenization_key = fields.Char(string='Tokenization Key ', groups='base.group_user')
    authorization_process = fields.Selection([('client_token', 'Client Token'),
                                              ('auth_token', 'Authorized token')
                                            ], string="Authorization Process", groups='base.group_user', default="client_token")
    brt_paypal_enabled = fields.Boolean(string="paypal Enabled", default=True)
    brt_version = fields.Selection([('old', 'Old'), ('new', 'New')], string="Version", default="new")

    @api.model
    def _get_compatible_acquirers(self, *args, currency_id=None, **kwargs):
        acquirers = super()._get_compatible_acquirers(*args, currency_id=currency_id, **kwargs)
        currency = self.env['res.currency'].browse(currency_id).exists()
        if currency and currency.name not in supported_currencies:
            acquirers = acquirers.filtered(lambda a: a.provider != 'braintree')
        return acquirers

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'braintree':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment_braintree.payment_method_braintree').id

    def _get_authorization_token(self, merchant_account_id):
        self.ensure_one()
        if self.brt_tokenization_key and self.authorization_process == 'auth_token' and not self.enable_3d_secure:
            return {
                'status': True,
                'token': self.brt_tokenization_key
            }
        BraintreeConn = self._braintree_setup()
        return BraintreeConn._get_client_token(merchant_account_id)

    def _braintree_setup(self):
        self.ensure_one()
        BraintreeConn = BraintreeConnector(
            merchant_id=self.brt_merchant_id,
            public_key=self.brt_public_key,
            private_key=self.brt_private_key,
            environment='production' if self.state=='enabled' else 'sandbox'
        )
        return BraintreeConn

    def _get_merchant_account_id(self, currency):
        self.ensure_one()
        if not self.brt_multicurrency:
            return self.brt_merchant_account_id
        merchant_account = self.multicurrency_ids.filtered(lambda r: r.braintree_merchant_currency.name == currency and r.braintree_merchant_validate)
        if merchant_account:
            return merchant_account[0].braintree_merchant_id
        return False

    def _fetch_merchant_account_id(self, merchant_account_id):
        self.ensure_one()
        BraintreeConn = self.sudo()._braintree_setup()
        return BraintreeConn._fetch_merchant_account(merchant_account_id)

    def _validate_merchant_account_id(self, currency, merchant_account_id, debug=False):
        result = {
            'status': False,
            'message': _("%s payment gateway not configure for '%s'. Please connect your shop provider.") % (self.name, currency)
        }
        self.ensure_one()
        if not merchant_account_id:
            return  result
        resp = self._fetch_merchant_account_id(merchant_account_id)
        if resp['status'] and resp['account_status'] == 'active' and resp['account_currency'] == currency:
            return {
                'status': True,
                'currency': currency,
                'merchant_account_id': merchant_account_id
            }
        if not resp['status']:
            return resp

        if debug:
            if resp['account_status'] != 'active':
                result['message'] = _('Merchant account id not in active state.')
            if resp['account_currency'] != currency:
                result['message'] = _('Currency not match with merchant account id.')
        return result

    def _process_merchant_account_id(self, currency):
        merchant_account_id = self.sudo()._get_merchant_account_id(currency)
        return self._validate_merchant_account_id(currency, merchant_account_id)

    def _create_braintree_transaction(self, values):
        BraintreeConn = self.sudo()._braintree_setup()
        if self and self.allow_tokenization and values.get('options'):
            values.get('options').update({
                "store_in_vault_on_success": True,
            })
        return BraintreeConn._create_transaction(values)
    
    def _braintree_token_payment(self, payload=None):
        BraintreeConn = self.sudo()._braintree_setup()
        return BraintreeConn._create_transaction(payload)
    
    def _create_braintree_token(self, values):
        BraintreeConn = self.sudo()._braintree_setup()
        return BraintreeConn._create_payment_method(values)

    def _braintree_action_url(self):
        self.ensure_one()
        return '/payment/braintree'
