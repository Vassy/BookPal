
import logging
from datetime import datetime, date, timedelta
from threading import Thread
from odoo import fields, models, api, _, registry, SUPERUSER_ID
from odoo.exceptions import UserError

_logger = logging.getLogger("BigCommerce")


class BigCommerceStoreConfiguration(models.Model):
    _inherit = "bigcommerce.store.configuration"

    last_import_products_date = fields.Date('Last Import Products Date')

    def bigcommerce_to_odoo_import_pricelist_main(self):
        """Import main pricelist."""
        self.bigcommerce_operation_message = \
            "Import Pricelist Process Running..."
        self._cr.commit()
        dbname = self.env.cr.dbname
        db_registry = registry(dbname)
        with api.Environment.manage(), db_registry.cursor() as cr:
            env_thread1 = api.Environment(cr, SUPERUSER_ID, self._context)
            t = Thread(target=self.bigcommerce_to_odoo_import_pricelist,
                       args=())
            t.start()

    def bigcommerce_to_odoo_import_pricelist(self):
        """Import pricelist."""
        with api.Environment.manage():
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))
            pricelist_obj = self.env['product.pricelist']
            import_pricelist = pricelist_obj.with_user(
                1).bigcommerce_to_odoo_import_pricelist(self)
            return import_pricelist

    def bigcommerce_to_odoo_import_products(self, store_id=None):
        """
        Func: This method use to import products from bigcommerce to odoo
        :return: True
        """
        bigcommerce_store_obj = self.search([('id', '=', store_id)])
        product_obj = self.env['product.template']
        if bigcommerce_store_obj:
            _logger.info("===== Auto Import Bigcommerce Products =====")
            bc_from_date = bigcommerce_store_obj.last_import_products_date
            from_date = bc_from_date + timedelta(days=-1)
            if not from_date:
                from_date = date.today() - timedelta(days=1)
            product_obj.with_context(from_date=from_date).import_product_from_bigcommerce(
                bigcommerce_store_obj.warehouse_id, bigcommerce_store_obj)
            bigcommerce_store_obj.last_import_products_date = datetime.today()
        else:
            raise UserError(_("No record found of Bigcommerce store."))
