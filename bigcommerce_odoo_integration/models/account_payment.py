from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    gateway_transaction_id = fields.Char('BC Gatway Transaction Id')
