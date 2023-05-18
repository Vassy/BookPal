# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class BestSellerReport(models.TransientModel):
    _name = "update.seller.report"
    _description = "Update Seller Report"

    never_report = fields.Boolean(string="Never Report")
    report_type = fields.Selection(
        [
            ("individual", "Individual"),
            ("bulk", "Bulk"),
            ("mixed", "Mixed"),
        ],
        string="Report Type",
    )
    fulfilment_project = fields.Boolean(string="Fulfilment Project")
    reported = fields.Boolean(string="Reported")

    @api.onchange("fulfilment_project")
    def onchange_fulfilment_project(self):
        if self.fulfilment_project:
            self.report_type = "individual"

    def update_seller_report(self):
        active_ids = self.env[self._context.get("active_model")].browse(
            self._context.get("active_ids")
        )
        if self.never_report:
            active_ids.mapped("product_id").write(
                {"is_never_report": self.never_report}
            )
        sale_data = {"fulfilment_project": self.fulfilment_project}
        if self.report_type:
            sale_data.update({"report_type": self.report_type})
        if self.reported:
            sale_data.update({"reported": self.reported})
        active_ids.mapped("order_id").write(sale_data)
