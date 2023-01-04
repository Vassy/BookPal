import json
from requests import request
from threading import Thread
from odoo import fields, models, api, _, registry, SUPERUSER_ID
from dateutil.relativedelta import relativedelta
import logging
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger("BigCommerce")

class BigCommerceStoreConfiguration(models.Model):
    _inherit = "bigcommerce.store.configuration"

    def bigcommerce_to_odoo_import_pricelist_main(self):
        self.bigcommerce_operation_message = "Import Pricelist Process Running..."
        self._cr.commit()
        dbname = self.env.cr.dbname
        db_registry = registry(dbname)
        with api.Environment.manage(), db_registry.cursor() as cr:
            env_thread1 = api.Environment(cr, SUPERUSER_ID, self._context)
            t = Thread(target=self.bigcommerce_to_odoo_import_pricelist,
                       args=())
            t.start()

    def bigcommerce_to_odoo_import_pricelist(self):
        with api.Environment.manage():
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))
            pricelist_obj = self.env['product.pricelist']
            import_pricelist = pricelist_obj.with_user(1).bigcommerce_to_odoo_import_pricelist(self)
            return import_pricelist