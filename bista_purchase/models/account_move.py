# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_pick_note = fields.Html('Common Notes')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def create(self, vals):
        res = super(AccountMoveLine, self).create(vals)
        for move_line in res:
            invoiced_status_id = self.env.ref('bista_purchase.status_line_invoiced')
            move_line.purchase_line_id.status_id = invoiced_status_id.id
        return res
