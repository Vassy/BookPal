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
    _name = "bigcommerce.store.configuration"
    _description = 'BigCommerce Store Configuration'

    name = fields.Char(required=True, string="Name")
    active = fields.Boolean('Active', default=True)
    bigcommerce_store_hash = fields.Char(string="Store Hash")
    bigcommerce_x_auth_client = fields.Char(string="X-Auth-Client", help="X-Auth-Client", copy=False)
    bigcommerce_x_auth_token = fields.Char(copy=False, string='X-Auth-Token', help="X-Auth-Token")
    bigcommerce_api_url = fields.Char(copy=False, string='API URL',
                                      help="API URL, Redirect to this URL when calling the API.",
                                      default="https://api.bigcommerce.com/stores/")
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
    from_order_date = fields.Datetime(string='From Date')
    last_modification_date = fields.Datetime(string="To Date")
    bigcommerce_operation_message = fields.Char(string="Bigcommerce Message", help="bigcommerce_operation_message",
                                                copy=False)
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse")
    bigcommerce_product_skucode = fields.Boolean("Check Bigcommerce Product Skucode")
    source_of_import_data = fields.Integer(string="Source(Page) Of Import Data", default=1)
    destination_of_import_data = fields.Integer(string="Destination(Page) Of Import Data", default=1)
    auto_import_orders = fields.Boolean("Auto Import Orders", help="If True then automatically import all orders.")
    from_product_id = fields.Integer(string='From Product ID')
    to_product_id = fields.Integer(string='To Product ID')
    bc_customer_prefix = fields.Char(string='Customer Prefix',help="Enter string if you want to add prefix before customer id. \nExample. bigcommerce customer id = 44154, prefix string = MyStore So final customer id will be MyStore44154.")
    bigcommerce_product_import_status = fields.Char(string="Product Import Message",
                                                    help="show status of import product process", copy=False)
    bigcommerce_product_id = fields.Char(string='Bigcommerce Product ID')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')

    # kanban view field
    color = fields.Integer(string='Color Index', help="select color")
    image = fields.Binary(string="Image", help="Select Image.")
    image_medium = fields.Binary(string="Medium Size Image", related="image", store=True, )
    image_small = fields.Binary(string="Large Size Image", related="image", store=True, )
    total_order_count = fields.Integer(string='Orders', compute='get_kanban_counts')
    total_product_count = fields.Integer(string='Products', compute='get_kanban_counts')
    total_customer_count = fields.Integer(string='Customers', compute='get_kanban_counts')
    auto_import_inventory_from_bigcommerce = fields.Boolean(string='Auto import inventory from bigcommerce')
    bigcommerce_order_status_ids = fields.Many2many('bigcommerce.order.status', string='Order Status')

    def create_cron_for_automation_task(self, cron_name, model_name, code_method, interval_number=10,
                                        interval_type='minutes', numbercall=1, nextcall_timegap_minutes=10):
        self.env['ir.cron'].create({
            'name': cron_name,
            'model_id': self.env['ir.model'].search([('model', '=', model_name)]).id,
            'state': 'code',
            'code': code_method,
            'interval_number': interval_number,
            'interval_type': interval_type,
            'numbercall': numbercall,
            'nextcall': datetime.now() + timedelta(minutes=nextcall_timegap_minutes),
            'doall': True,
        })
        return True


    def auto_import_bigcommerce_orders(self):
        store_ids = self.sudo().search([('auto_import_orders', '!=', False)])
        for store_id in store_ids:
            for bigcommerce_order_status_id in store_id.bigcommerce_order_status_ids:
                sale_order_obj = self.env['sale.order']
                last_modification_date = datetime.now() - relativedelta(days=15)
                today_date = datetime.now() + relativedelta(hours=5)
                total_pages = 2
                sale_order_obj.with_user(1).bigcommerce_to_odoo_import_orders(store_id.warehouse_id, store_id,last_modification_date,today_date,total_pages,bigcommerce_order_status_id)

    def bigcommerce_import_operation_wizard(self):
        return self.env.ref('bigcommerce_odoo_integration.action_bc_import_operation').read()[0]

    def bigcommerce_export_operation_wizard(self):
        return self.env.ref('bigcommerce_odoo_integration.action_bc_export_operation').read()[0]

    def update_all_products_inventory(self):
        product_obj = self.env['product.template']
        total_product_ids = product_obj.search([('bigcommerce_product_id','!=',False)])
        if total_product_ids:
            last_id = 0
            timegap = 10
            while True:
                product_ids = product_obj.search([('id', '>', last_id),('id','in',total_product_ids.ids),('inventory_tracking','!=','none')], limit=200, order='id')
                if product_ids:
                    last_id = product_ids.ids[-1]
                    cron_name = "Bigcommerce : Background Update Inventory {0} to {1}".format(self.name, last_id)
                    model_name = 'product.template'
                    code_method = 'model.update_product_inventory_cron({0},{1},{2})'.format(product_ids.ids,self.id,True)
                    self.create_cron_for_automation_task(cron_name, model_name, code_method,
                                                                   interval_type='minutes', interval_number=10,
                                                                   numbercall=1, nextcall_timegap_minutes=timegap)
                    timegap += 5
                else:
                    return

    def auto_update_all_product_inventory_cron(self):
        bc_config_id = self.env['bigcommerce.store.configuration'].search([])
        for bc_config in bc_config_id:
            bc_config.update_all_products_inventory()

    def delete_unwanted_crons_of_update_stock_in_bc(self):
        self._cr.execute(
            "delete from ir_cron where active = False and cron_name like '%Bigcommerce : Background Update Inventory%'")

    def create_bigcommerce_operation(self, operation, operation_type, bigcommerce_store_id, log_message, warehouse_id):
        vals = {
            'bigcommerce_operation': operation,
            'bigcommerce_operation_type': operation_type,
            'bigcommerce_store': bigcommerce_store_id and bigcommerce_store_id.id,
            'bigcommerce_message': log_message,
            'warehouse_id': warehouse_id and warehouse_id.id or False
        }
        operation_id = self.env['bigcommerce.operation'].create(vals)
        return operation_id

    def create_bigcommerce_operation_detail(self, operation, operation_type, req_data, response_data, operation_id,
                                            warehouse_id=False, fault_operation=False, process_message=False):
        bigcommerce_operation_details_obj = self.env['bigcommerce.operation.details']
        vals = {
            'bigcommerce_operation': operation,
            'bigcommerce_operation_type': operation_type,
            'bigcommerce_request_message': '{}'.format(req_data),
            'bigcommerce_response_message': '{}'.format(response_data),
            'operation_id': operation_id.id,
            'warehouse_id': warehouse_id and warehouse_id.id or False,
            'fault_operation': fault_operation,
            'process_message': process_message,
        }
        operation_detail_id = bigcommerce_operation_details_obj.create(vals)
        return operation_detail_id

    def update_request_from_odoo_to_bigcommerce(self, body=False, api_operation=False):
        headers = {"Accept": "application/json",
                   "X-Auth-Client": "{}".format(self.bigcommerce_x_auth_client),
                   "X-Auth-Token": "{}".format(self.bigcommerce_x_auth_token),
                   "Content-Type": "application/json"}
        data = json.dumps(body)
        _logger.info("Dump Product Data : {}".format(data))
        url = "{0}{1}{2}".format(self.bigcommerce_api_url, self.bigcommerce_store_hash, api_operation)
        try:
            _logger.info("Send PUT Request From odoo to BigCommerce: {0}".format(url))
            return request(method='PUT', url=url, data=data, headers=headers)
        except Exception as e:
            _logger.info("Getting an Error in PUT Req odoo to BigCommerce: {0}".format(e))
            return e

    def send_request_from_odoo_to_bigcommerce(self, body=False, api_operation=False):
        headers = {"Accept": "application/json",
                   "X-Auth-Client": "{}".format(self.bigcommerce_x_auth_client),
                   "X-Auth-Token": "{}".format(self.bigcommerce_x_auth_token),
                   "Content-Type": "application/json"}
        data = json.dumps(body)
        url = "{0}{1}{2}".format(self.bigcommerce_api_url, self.bigcommerce_store_hash, api_operation)
        try:
            _logger.info("Send POST Request From odoo to BigCommerce: {0}".format(url))
            return request(method='POST', url=url, data=data, headers=headers)
        except Exception as e:
            _logger.info("Getting an Error in POST Req odoo to BigCommerce: {0}".format(e))
            return e

    def send_get_request_from_odoo_to_bigcommerce(self, api_operation=False):
        headers = {"Accept": "application/json",
                   "X-Auth-Client": "{}".format(self.bigcommerce_x_auth_client),
                   "X-Auth-Token": "{}".format(self.bigcommerce_x_auth_token),
                   "Content-Type": "application/json"}
        #
        url = "{0}{1}{2}".format(self.bigcommerce_api_url, self.bigcommerce_store_hash, api_operation)
        try:
            _logger.info("Send GET Request From odoo to BigCommerce: {0}".format(url))
            return request(method='GET', url=url, headers=headers)
        except Exception as e:
            _logger.info("Getting an Error in GET Req odoo to BigCommerce: {0}".format(e))
            return e

    def bigcommerce_to_odoo_import_product_brands_main(self):
        self.bigcommerce_operation_message = "Import Product Brand Process Running..."
        self._cr.commit()
        dbname = self.env.cr.dbname
        db_registry = registry(dbname)
        with api.Environment.manage(), db_registry.cursor() as cr:
            env_thread1 = api.Environment(cr, SUPERUSER_ID, self._context)
            t = Thread(target=self.bigcommerce_to_odoo_import_product_brands, args=())
            t.start()

    def bigcommerce_to_odoo_import_product_brands(self):
        with api.Environment.manage():
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))
            product_brand_obj = self.env['bc.product.brand']
            import_brand = product_brand_obj.bigcommerce_to_odoo_import_product_brands(self.warehouse_id,
                                                                                       self)
            self._cr.close()
            return import_brand

    def bigcommerce_to_odoo_import_product_categories_main(self):
        self.bigcommerce_operation_message = "Import Product Categories Process Running..."
        self._cr.commit()
        dbname = self.env.cr.dbname
        db_registry = registry(dbname)
        with api.Environment.manage(), db_registry.cursor() as cr:
            env_thread1 = api.Environment(cr, SUPERUSER_ID, self._context)
            t = Thread(target=self.bigcommerce_to_odoo_import_product_categories, args=())
            t.start()

    def bigcommerce_to_odoo_import_product_categories(self):
        with api.Environment.manage():
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))
            product_category_obj = self.env['product.category']
            import_categories = product_category_obj.bigcommerce_to_odoo_import_product_categories(self.warehouse_id,
                                                                                                   self)
            self._cr.close()
            return import_categories

    def import_product_from_bigcommerce_main(self):
        self.bigcommerce_operation_message = "Import Product Process Running..."
        self._cr.commit()
        dbname = self.env.cr.dbname
        db_registry = registry(dbname)
        with api.Environment.manage(), db_registry.cursor() as cr:
            env_thread1 = api.Environment(cr, SUPERUSER_ID, self._context)
            t = Thread(target=self.import_product_from_bigcommerce, args=())
            t.start()

    def import_product_from_bigcommerce(self,source_page=1,destination_page=1):
        with api.Environment.manage():
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))
            product_obj = self.env['product.template']
            import_product = product_obj.import_product_from_bigcommerce(self.warehouse_id, self,source_page=source_page,destination_page=destination_page)
            self._cr.close()
            return import_product

    def bigcommerce_to_odoo_import_customers_main(self):
        self.bigcommerce_operation_message = "Import Customer Process Running..."
        self._cr.commit()
        dbname = self.env.cr.dbname
        db_registry = registry(dbname)
        with api.Environment.manage(), db_registry.cursor() as cr:
            env_thread1 = api.Environment(cr, SUPERUSER_ID, self._context)
            t = Thread(target=self.bigcommerce_to_odoo_import_customers, args=())
            t.start()

    def bigcommerce_to_odoo_import_customers(self,source_page=1,destination_page=1):
        with api.Environment.manage():
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))
            customer_obj = self.env['res.partner']
            import_customer = customer_obj.bigcommerce_to_odoo_import_customers(self.warehouse_id, self,source_page=source_page,destination_page=destination_page)
            self._cr.close()
            return import_customer

    # def bigcommerce_to_odoo_import_inventory_main(self):
    #     product_inventory = self.env['stock.inventory']
    #     import_inventory = product_inventory.bigcommerce_to_odoo_import_inventory(self.warehouse_id, self)
    #     return import_inventory

    def bigcommerce_to_odoo_import_orders_main(self,from_date=False,to_date=False,bigcommerce_order_status_ids=False):
        sale_order_obj = self.env['sale.order']
        sale_order_obj.with_user(1).bigcommerce_to_odoo_import_orders(self.warehouse_id, self,
                                                                      last_modification_date=from_date,
                                                                      today_date=to_date,
                                                                      bigcommerce_order_status_ids=bigcommerce_order_status_ids)
        # self.bigcommerce_operation_message = "Import Sale Order Process Running..."
        # self._cr.commit()
        # dbname = self.env.cr.dbname
        # db_registry = registry(dbname)
        # with api.Environment.manage(), db_registry.cursor() as cr:
        #     env_thread1 = api.Environment(cr, SUPERUSER_ID, self._context)
        #     t = Thread(target=self.bigcommerce_to_odoo_import_orders, args=(from_date,to_date,bigcommerce_order_status_ids))
        #     t.start()

    def bigcommerce_to_odoo_import_orders(self,from_date=False,to_date=False,bigcommerce_order_status_ids=False):
        with api.Environment.manage():
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))
            sale_order_obj = self.env['sale.order']
            import_order = sale_order_obj.with_user(1).bigcommerce_to_odoo_import_orders(self.warehouse_id, self,last_modification_date=from_date,today_date=to_date,bigcommerce_order_status_ids=bigcommerce_order_status_ids)
            self._cr.close()
            return import_order

    def bigcommerce_customers(self):
        """
        :return: this method return customer list view
        :rtype: view
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bigcommerce Customers',
            'view_mode': 'tree,form',
            'context': {'create': False},
            'domain': [('bigcommerce_store_id', '!=', False)],
            'res_model': 'res.partner',
            'target': 'current'
        }

    def bigcomerce_products(self):
        """
        :return: this method return product list view
        """
        if self.bigcommerce_store_type == 'b2b':
            domain = "[('bigcommerce_product_id', '!=', False)]"
        else:
            domain = "[('b2c_bigcommerce_product_id', '!=', False)]"
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bigcommerce Products',
            'view_mode': 'tree,form',
            'res_model': 'product.template',
            'domain': domain,
            'context': {'create': False},
            'target': 'current'
        }

    def bigcommerce_orders(self):
        """
        :return: this method return order view
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bigcommerce Orders',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('bigcommerce_store_id', '=', self.id)],
            'context': {'create': False},
            'target': 'current'
        }

    def bigcommerce_to_odoo_import_customer_groups(self):
        """
        :return: this method import customer groups from bigcommerce
        """
        try:

            url = "%s%s/v2/customer_groups" % (self.bigcommerce_api_url, self.bigcommerce_store_hash)
            headers = {"Accept": "application/json",
                       "X-Auth-Client": "{}".format(self.bigcommerce_x_auth_client),
                       "X-Auth-Token": "{}".format(self.bigcommerce_x_auth_token),
                       "Content-Type": "application/json"}

            _logger.info(">>>> sending get request to {}".format(url))
            response_data = request(method="GET", url=url, headers=headers)
            if response_data.status_code in [200, 201]:
                _logger.info(">> get successfully response from {}".format(url))
                response_data = response_data.json()
                bc_customer_group_obj = self.env['bigcommerce.customer.group']
                for data in response_data:
                    bc_customer_group_id = bc_customer_group_obj.sudo().search(
                        [('customer_group_id', '=', data.get('id')),('bc_store_id','=',self.id)])
                    if not bc_customer_group_id:
                        customer_group_data = {
                            'name': data.get('name'),
                            'customer_group_id': data.get('id'),
                            'bc_store_id':self.id
                        }
                        bc_customer_group_obj.sudo().create(customer_group_data)
                        self._cr.commit()
                        _logger.info(">>>> sucessfully create customer group name {}".format(data.get('name')))
                    else:
                        customer_group_data = {
                            'name': data.get('name')
                        }
                        bc_customer_group_obj.sudo().write(customer_group_data)
                        self._cr.commit()
                        _logger.info(">>>> successfully update customer group name {}".format(data.get('name')))

            elif (response_data.status_code in [204]) and not response_data.text:
                _logger.info("There are no customer groups in your store.")
            else:
                raise ValidationError(
                    _("Getting some error from {0} \n response :- {1}".format(url, response_data.text)))

        except Exception as error:
            raise ValidationError(error)

    # # UI Instance
    # def import_product_categories_brand(self):
    #     self.bigcommerce_to_odoo_import_product_brands_main()
    #     self.bigcommerce_to_odoo_import_product_categories_main()
    #     return True
    #
    # def import_customer_and_group(self):
    #     self.bigcommerce_to_odoo_import_customers_main()
    #     self.bigcommerce_to_odoo_import_customer_groups()
    #     return True

    def open_bigcommerce_store_form_view(self):
        form_id = self.env.ref('bigcommerce_odoo_integration.bigcommerce_store_configuration_form_view')
        return {
            'name': 'Store Configuration',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'context': self._context,
            'views': [(form_id.id, 'form')],
            'res_id': self.id,
            'res_model': 'bigcommerce.store.configuration',
        }

    def action_redirect_to_product(self):
        action = self.env.ref('sale.product_template_action').read()[0]
        listing_id = self.env['bc.store.listing'].sudo().search([('bigcommerce_store_id', '=', self.id)]).mapped('product_tmpl_id')
        # action['domain'] = [('bigcommerce_store_id', '=', self.id)]
        action['domain'] = [('id', 'in', listing_id.ids)]
        return action

    def action_redirect_to_order(self):
        action = self.env.ref('sale.action_orders').read()[0]
        action['domain'] = [('bigcommerce_store_id', '=', self.id)]
        return action

    def action_redirect_to_customers(self):
        action = self.env.ref('bigcommerce_odoo_integration.bigcommerce_customer_action_form').read()[0]
        action['domain'] = [('bigcommerce_store_id', '=', self.id)]
        return action

    def get_kanban_counts(self):
        for market_id in self:
            market_id.total_customer_count = self.env['res.partner'].sudo().search_count(
                [('bigcommerce_store_id', '=', market_id.id)])
            market_id.total_order_count = self.env['sale.order'].sudo().search_count(
                [('bigcommerce_store_id', '=', market_id.id)])
            # market_id.total_product_count = self.env['product.template'].sudo().search_count(
            #     [('bigcommerce_store_id', '=', market_id.id)])
            market_id.total_product_count = self.env['bc.store.listing'].sudo().search_count([('bigcommerce_store_id', '=', market_id.id)])

    def action_redirect_to_process(self):
        action = self.env.ref('bigcommerce_odoo_integration.action_bigcommerce_operation').read()[0]
        return action
