# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

import logging
from threading import Thread
from odoo import fields, models, api, _, registry, SUPERUSER_ID
from odoo.exceptions import UserError

_logger = logging.getLogger("BigCommerce")


class BigCommerceImportOperation(models.TransientModel):
    _name = "bigcommerce.import.operation"
    _description = "Import Operation of Bigcommerce"

    def _get_default_marketplace(self):
        return self.env['bigcommerce.store.configuration'].browse(self.env.context['active_id'])

    bc_store_instance_id = fields.Many2one("bigcommerce.store.configuration", string="BigCommerce Store",
                                           default=_get_default_marketplace)
    import_product_category = fields.Boolean(string="Product Category")
    import_operation_of_bc = fields.Selection(
        [('import_pc_pg_grp', 'Product Category, Brand, Group'), ('import_customer', 'Customer'),
         ('import_products', 'Products'), ('import_order', 'Orders')], string="Import", default="import_pc_pg_grp")
    import_product_bc_id_wise = fields.Boolean(string='Import Product Using BigCommerce ID',
                                               help='Enter Bigcommerce ID')
    bc_product_id = fields.Char(string="BigCommerce Product ID",
                                help="Use BigCommerce Product ID if you want to list specific product.")
    import_order_bc_id_wise = fields.Boolean(
        string='Import Order Using BigCommerce ID',
        help='Enter Bigcommerce Order ID')
    bc_order_id = fields.Char(
        string="BigCommerce Order ID",
        help="Use BigCommerce Order ID if you want to list specific order.")
    import_order_date_wise = fields.Boolean(
        string='Import Order Using Dates',
        help='Enter Bigcommerce Order ID')
    from_order_date = fields.Datetime(string='From Date')
    to_order_date = fields.Datetime(string="To Date")
    source_of_import_data = fields.Integer(
        string="Source(Page) Of Import Data", default=1)
    destination_of_import_data = fields.Integer(
        string="Destination(Page) Of Import Data", default=1)
    bigcommerce_order_status = fields.Selection([('0', '0 - Incomplete'),
                                                 ('1', '1 - Pending'),
                                                 ('2', '2 - Shipped'),
                                                 ('3', '3 - Partially Shipped'),
                                                 ('4', '4 - Refunded'),
                                                 ('5', '5 - Cancelled'),
                                                 ('6', '6 - Declined'),
                                                 ('7', '7 - Awaiting Payment'),
                                                 ('8', '8 - Awaiting Pickup'),
                                                 ('9', '9 - Awaiting Shipment'),
                                                 ('10', '10 - Completed'),
                                                 ('11', '11 - Awaiting Fulfillment'),
                                                 ('12', '12 - Manual Verification Required'),
                                                 ('13', '13 - Disputed'),
                                                 ('14', '14 - Partially Refunded')], default='11')
    bigcommerce_order_status_ids = fields.Many2many(
        'bigcommerce.order.status', string='Order Status')

    def do_import_operations(self):
        dbname = self.env.cr.dbname
        db_registry = registry(dbname)
        if not self.bc_store_instance_id:
            raise UserError(_("Please select bigcommerce store to process."))
        if self.import_operation_of_bc == 'import_pc_pg_grp':
            self.bc_store_instance_id.bigcommerce_to_odoo_import_product_brands_main()
            self.bc_store_instance_id.bigcommerce_to_odoo_import_product_categories_main()
            self.bc_store_instance_id.bigcommerce_to_odoo_import_customer_groups()
        elif self.import_operation_of_bc == 'import_customer':
            # self.bc_store_instance_id.bigcommerce_to_odoo_import_customers_main()
            self.bc_store_instance_id.bigcommerce_operation_message = "Import Customer Process Running..."
            self._cr.commit()
            with api.Environment.manage(), db_registry.cursor() as cr:
                env_thread1 = api.Environment(cr, SUPERUSER_ID, self._context)
                t = Thread(target=self.bc_store_instance_id.bigcommerce_to_odoo_import_customers,
                           args=(self.source_of_import_data, self.destination_of_import_data))
                t.start()
        elif self.import_operation_of_bc == 'import_products':
            product_obj = self.env['product.template']
            if self.import_product_bc_id_wise:
                product_obj.import_product_from_bigcommerce(self.bc_store_instance_id.warehouse_id,
                                                            self.bc_store_instance_id, self.bc_product_id,
                                                            add_single_product=True)
            else:
                self.bc_store_instance_id.bigcommerce_operation_message = "Import Product Process Running..."
                self._cr.commit()
                with api.Environment.manage(), db_registry.cursor() as cr:
                    env_thread1 = api.Environment(
                        cr, SUPERUSER_ID, self._context)
                    t = Thread(target=self.bc_store_instance_id.import_product_from_bigcommerce,
                               args=(self.source_of_import_data, self.destination_of_import_data))
                    t.start()
        elif self.import_operation_of_bc == 'import_order':
            if self.import_order_bc_id_wise:
                self.env['sale.order'].with_context(
                    import_wizard_id=self,
                    big_commerce_order_id=self.bc_order_id).\
                    bigcommerce_to_odoo_import_orders(
                        warehouse_id=self.bc_store_instance_id.warehouse_id,
                        bigcommerce_store_ids=self.bc_store_instance_id,
                        total_pages=2, bigcommerce_order_status_ids=[])
            elif self.import_order_date_wise:
                self.bc_store_instance_id.\
                    bigcommerce_to_odoo_import_orders_main(
                        self.from_order_date,
                        self.to_order_date,
                        self.bigcommerce_order_status_ids)

    def run_cron_manually(self):
        """Execute the cron manually to import order."""
        self.bc_store_instance_id.auto_import_bigcommerce_orders()
