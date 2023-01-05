from odoo import fields, models

import logging
_logger = logging.getLogger("BigCommerce")

class ResCompany(models.Model):
    _inherit = "res.company"

    payment_journal_id = fields.Many2one('account.journal',string='Payment Journal')