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

    date_type = fields.Selection(
        [("date_order", "Order Date"), ("report_date", "Report Date")],
        string="Filter Date Type",
        required=True,
        default="date_order",
    )
    start_date = fields.Date(
        string="Start Date", default=datetime.datetime.today().replace(day=1)
    )
    end_date = fields.Date(string="End Date", default=fields.Date.context_today)
    report_type = fields.Selection(
        [
            ("individual", "Individual"),
            ("bulk", "Bulk"),
            ("mixed", "Mixed"),
        ],
        string="Report Type",
    )
    industry_ids = fields.Many2many(
        "res.partner.industry", string="Exclude Customer Segments"
    )

    def open_best_seller_report(self):
        ctx = dict(
            self.env.context,
            date_type=self.date_type,
            start_date=self.start_date,
            end_date=self.end_date,
            report_type=self.report_type,
            industry_ids=self.industry_ids.ids,
            display_default_code=False,
        )
        self.env["best.seller.report"].with_context(**ctx).init()
        return {
            "type": "ir.actions.act_window",
            "name": _("Best Seller Report"),
            "view_mode": "list,pivot",
            "res_model": "best.seller.report",
            "context": ctx,
        }
