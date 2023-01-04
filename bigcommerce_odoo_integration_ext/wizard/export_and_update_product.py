
import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class UpdateProductPricelist(models.TransientModel):
    _inherit = "export.and.update.product.to.bc"

    def update_product_pricelist_from_bc_to_odoo(self):
        product_templates = self.env['product.template'].browse(self._context.get('active_ids', []))
        for bc_store in self.bigcommerce_store_ids:
            self.env['product.template'].create_or_update_product_pricelist(bc_store,product_templates)
