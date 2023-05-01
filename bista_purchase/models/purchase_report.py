# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    order_process_time = fields.Integer("Average Processing Time", group_operator="avg")
    sale_order_date = fields.Datetime("Sales Order Date")
    date_planned = fields.Datetime("MAB Date")

    def _select(self):
    	select_str = super()._select() + ", po.order_process_time, po.sale_order_date, po.date_planned"
    	return select_str
