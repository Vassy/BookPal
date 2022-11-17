# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class SaleOrderRejectReason(models.TransientModel):
    _name = "reject.reason.wiz"
    _description = "Reason for Rejection"

    sale_id = fields.Many2one('sale.order')
    note = fields.Text(string='Reason for rejection')

    def update_reject_reason(self):
        sale_order = self.sale_id
        if sale_order:
            sale_order.state = 'draft'
            sale_order.action_draft()
            context = self._context
            self.env['sale.approval.log'].create({
                'sale_id': sale_order.id,
                'action_user_id': context.get('uid'),
                'done_action': 'Quote Rejected',
                'action_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'note': self.note or '',
            })
