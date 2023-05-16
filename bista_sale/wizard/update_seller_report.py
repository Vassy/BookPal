# -*- encoding: utf-8 -*-

from odoo import models, fields


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

    def update_seller_report(self):
        print(self.never_report, self.report_type, self.fulfilment_project)
        active_ids = self.env[self._context.get("active_model")].browse(
            self._context.get("active_ids")
        )
        print(active_ids)
        if self.never_report:
            active_ids.mapped("product_id").write(
                {"is_never_report": self.never_report}
            )
        if self.report_type:
            active_ids.mapped("order_id").write({"report_type": self.report_type})
        if self.fulfilment_project:
            active_ids.mapped("order_id").write(
                {"fulfilment_project": self.fulfilment_project}
            )
        if self.reported:
            active_ids.mapped("order_id").write({"reported": self.reported})
