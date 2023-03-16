from odoo import fields, models, api


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("manual", "Manual")], ondelete={"manual": "set default"}
    )

    @api.onchange("delivery_type")
    def _onchange_delivery_type(self):
        if self.delivery_type == "manual":
            self.integration_level = "rate"
