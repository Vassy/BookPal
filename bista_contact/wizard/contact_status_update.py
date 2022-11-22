# -*- coding: utf-8 -*-
from odoo import _, fields, models


class ContactStatusUpdate(models.TransientModel):
    _name = 'contact.status.update'
    _description='Contact Status Update'

    reason=fields.Char(string="Reason")
    block=fields.Boolean('Block')


    def update_status(self):
        """ to block customer"""
        if self.env.context.get('partner_ids'):
            active_ids = self.env.context.get('partner_ids')
            if active_ids:
               res_ids = self.env['res.partner'].browse(active_ids)
            for res in res_ids:
                 res.block_reason = self.reason
                 res.block =True

    def unblock_update_status(self):
        """ to unblock customer"""
        if self.env.context.get('partner_ids'):
            active_ids = self.env.context.get('partner_ids')
            if active_ids:
                res_ids = self.env['res.partner'].browse(active_ids)
            for res in res_ids:
                res.block = False
