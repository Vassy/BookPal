
import logging

from odoo import models
from odoo.addons.bigcommerce_odoo_integration.models.\
    stock import StockPicking

_logger = logging.getLogger("BigCommerce")


class StockPickingExtend(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        """Skip to export shippment when export is disable in configuration."""
        print ("\n extend _action_done >>>")
        res = super(StockPicking, self)._action_done()
        if self.sale_id.bigcommerce_store_id and \
                self.sale_id.bigcommerce_store_id.bc_export_shipment:
            5 / 0
            customer_location_id = self.env.ref(
                'stock.stock_location_customers')
            if self.sale_id.bigcommerce_store_id and \
                    self.location_dest_id.id == customer_location_id.id:
                self.export_shipment_to_bigcommerce()
        return res

    StockPicking._action_done = _action_done
