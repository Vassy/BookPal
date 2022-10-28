# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from time import strftime

from odoo import models, fields, _, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def backorder_run_scheduler(self):

        today_datetime = datetime.now()
        today_date = today_datetime.date()
        next_day_start = (today_date + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        next_day_end = (today_date + timedelta(days=1)).strftime("%Y-%m-%d 23:59:59")
        next_week_start = (today_date + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        next_week_end = (today_date + timedelta(days=7)).strftime("%Y-%m-%d 23:59:59")

        day_backorder_ids = self.env['stock.picking'].search([('backorder_id', '!=', False),
                                                              ('picking_type_code', '=', 'incoming'),
                                                              ('state', 'not in', ('done', 'cancel')),
                                                              ('scheduled_date', '>=', next_day_start),
                                                              ('scheduled_date', '<=', next_day_end)])
        week_backorder_ids = self.env['stock.picking'].search([('backorder_id', '!=', False),
                                                               ('picking_type_code', '=', 'incoming'),
                                                               ('state', 'not in', ('done', 'cancel')),
                                                               ('scheduled_date', '>=', next_week_start),
                                                               ('scheduled_date', '<=', next_week_end)])
        template_one = self.env.ref('bista_purchase.email_template_purchase_reciept_first_reminder')
        template_second = self.env.ref('bista_purchase.email_template_purchase_reciept_second_reminder')

        if day_backorder_ids:
            for rec in day_backorder_ids:
                template_one.send_mail(rec.id, force_send=True)
        if week_backorder_ids:
            for record in week_backorder_ids:
                template_second.send_mail(record.id, force_send=True)
