# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2022 (https://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, _
import datetime


class BestSellerReport(models.TransientModel):
    _name = "best.seller.report.wiz"
    _description = "Best Seller Report"

    start_date = fields.Date(
        string="Start Date",
        default=datetime.datetime.today().replace(day=1))
    end_date = fields.Date(
        string="End Date",
        default=fields.Date.context_today)
    report_type = fields.Selection([
                ('individual', 'Individual'),
                ('bulk', 'Bulk'),
                ('mixed', 'Mixed'),
            ], string='Report Type')

    def open_best_seller_report(self):
        # view_id = self.env.ref('bista_sale.view_seller_report')
        ctx = dict(
            self.env.context,
            start_date=self.start_date,
            end_date=self.end_date,
            report_type=self.report_type,
            create=0,
        )
        self.env['best.seller.report'].with_context(ctx=ctx).init()
        return{
            'type': 'ir.actions.act_window',
            'name': _('Best Seller Report'),
            'view_mode': 'list,pivot',
            'res_model': 'best.seller.report',
            # 'views': [(view_id.id, 'tree')],
            'context': ctx,
        }