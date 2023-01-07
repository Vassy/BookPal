
import logging
from threading import Thread
from odoo import fields, models, api, _, registry, SUPERUSER_ID
from odoo.exceptions import UserError

_logger = logging.getLogger("BigCommerce")


def do_import_operations(self):
    """Do import operations."""
    dbname = self.env.cr.dbname
    db_registry = registry(dbname)
    if not self.bc_store_instance_id:
        raise UserError(_("Please select bigcommerce store to process."))
    if self.import_operation_of_bc == 'import_pc_pg_grp':
        self.bc_store_instance_id.\
            bigcommerce_to_odoo_import_product_brands_main()
        self.bc_store_instance_id.\
            bigcommerce_to_odoo_import_product_categories_main()
        self.bc_store_instance_id.\
            bigcommerce_to_odoo_import_customer_groups()
    elif self.import_operation_of_bc == 'import_customer':
        # self.bc_store_instance_id.bigcommerce_to_odoo_import_customers_main()
        self.bc_store_instance_id.bigcommerce_operation_message = \
            "Import Customer Process Running..."
        self._cr.commit()
        with api.Environment.manage(), db_registry.cursor() as cr:
            env_thread1 = api.Environment(cr, SUPERUSER_ID, self._context)
            t = Thread(
                target=self.bc_store_instance_id.
                bigcommerce_to_odoo_import_customers,
                args=(self.source_of_import_data,
                      self.destination_of_import_data))
            t.start()
    elif self.import_operation_of_bc == 'import_products':
        product_obj = self.env['product.template']
        if self.import_product_bc_id_wise:
            product_obj.import_product_from_bigcommerce(
                self.bc_store_instance_id.warehouse_id,
                self.bc_store_instance_id, self.bc_product_id,
                add_single_product=True)
        else:
            self.bc_store_instance_id.bigcommerce_operation_message = \
                "Import Product Process Running..."
            self._cr.commit()
            with api.Environment.manage(), db_registry.cursor() as cr:
                env_thread1 = api.Environment(cr, SUPERUSER_ID, self._context)
                t = Thread(
                    target=self.bc_store_instance_id.
                    import_product_from_bigcommerce,
                    args=(self.source_of_import_data,
                          self.destination_of_import_data))
                t.start()
    elif self.import_operation_of_bc == 'import_order':
        self.bc_store_instance_id.bigcommerce_to_odoo_import_orders_main(
            self.from_order_date, self.to_order_date,
            self.bigcommerce_order_status)
    elif self.import_operation_of_bc == 'import_pricelist':
        self.bc_store_instance_id.bigcommerce_to_odoo_import_pricelist_main()


class BigCommerceImportOperation(models.TransientModel):
    _inherit = "bigcommerce.import.operation"

    import_operation_of_bc = fields.Selection(
        selection_add=[("import_pricelist", "Pricelist")],
        ondelete={'import_operation': 'set default'})
