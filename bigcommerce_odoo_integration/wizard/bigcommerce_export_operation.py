# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import logging
from threading import Thread
from odoo import fields, models, api, _, registry, SUPERUSER_ID
from odoo.exceptions import UserError

_logger = logging.getLogger("BigCommerce")


class BigCommerceExportOperation(models.TransientModel):
    _name = "bigcommerce.export.operation"
    _description = "Export Operation of Bigcommerce"

    bc_store_instance_ids = fields.Many2many("bigcommerce.store.configuration", 'bc_export_opr_bc_store_conf',
                                             string="BigCommerce Store")
    export_operation_of_bc = fields.Selection(
        [('export_product', 'Export Product')], string="Export")
    product_tmpl_ids = fields.Many2many('product.template')

    def do_export_operations(self):
        if not self.bc_store_instance_ids:
            raise UserError(_("Please select bigcommerce store to process."))
        product_obj = self.env['product.template']
        if self.export_operation_of_bc == 'export_product':
            for bc_store in self.bc_store_instance_ids:
                export_products = []
                for product in self.product_tmpl_ids:
                    listing_id = self.env['bc.store.listing'].search(
                        [('bigcommerce_store_id', '=', bc_store.id),
                         ('product_tmpl_id', '=', product.id)])
                    if not listing_id:
                        export_products.append(product.id)
                products_to_export = product_obj.search([('id', 'in', export_products)])
                product_obj.export_product_in_bigcommerce_from_product(bc_store, products_to_export)
        # elif self.export_operation_of_bc == 'update_product':
        #     pass

    def do_export_customer(self):
        if not self.bc_store_instance_ids:
            raise UserError(_("Please select bigcommerce store to process."))
        partner_obj = self.env['res.partner']
        partner_ids = partner_obj.browse(self._context.get('active_ids'))
        partner_ids.export_customer_to_bigcommerce(bc_store_ids=self.bc_store_instance_ids)

