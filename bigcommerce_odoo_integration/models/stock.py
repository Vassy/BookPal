import time
from requests import request
from datetime import datetime
from odoo import models,api,fields,_
import logging
import json
from odoo.exceptions import ValidationError

_logger = logging.getLogger("BigCommerce")

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    bc_shipping_provider = fields.Char(string='Shipping Provider')
    bigcommerce_shimpment_id = fields.Char(string="Bigcommerce Shipment Numebr")

    def export_shipment_to_bigcommerce(self):
        if not self.sale_id.big_commerce_order_id and not self.carrier_tracking_ref:
            raise ValidationError("Order Not Exported in BC Or Tracking No not set you can't Export Shipment")
        self.sale_id.get_shipment_address_id()
        time.sleep(2)
        self.sale_id.get_order_product_id()
        bigcommerce_store_hash = self.sale_id.bigcommerce_store_id.bigcommerce_store_hash
        api_url = "%s%s/v2/orders/%s/shipments" % (
            self.sale_id.bigcommerce_store_id.bigcommerce_api_url, bigcommerce_store_hash,
            self.sale_id.big_commerce_order_id)
        bigcommerce_auth_token = self.sale_id.bigcommerce_store_id.bigcommerce_x_auth_token
        bigcommerce_auth_client = self.sale_id.bigcommerce_store_id.bigcommerce_x_auth_client

        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'X-Auth-Token': "{}".format(bigcommerce_auth_token),
                   'X-Auth-Client': "{}".format(bigcommerce_auth_client)}
        ls = []
        for line in self.move_lines.filtered(lambda mv:mv.quantity_done != 0.0):
            order_product_id = line.sale_line_id.order_product_id
            _logger.info("3___________ {0}".format(order_product_id))
            line_data = {
                "order_product_id": int(order_product_id),
                # "product_id": int(line.sale_line_id.product_id.bigcommerce_product_id),
                "quantity": line.quantity_done or 0.0,
            }
            _logger.info("Product Data {0}".format(line_data))
            ls.append(line_data)
        tracking_ref = self.carrier_tracking_ref.split("+")
        if len(tracking_ref) == 1:
            tracking_ref = tracking_ref
        else:
            tracking_ref = tracking_ref[0]
        request_data = {
            'tracking_number': tracking_ref,
            'order_address_id': self.sale_id.bigcommerce_shipment_address_id,
            'shipping_provider': 'fedex' if self.carrier_id.name=='FEDEX' else 'ups',
            'tracking_carrier': 'fedex' if self.carrier_id.name=='FEDEX' else 'ups',
            'items': ls
        }
        operation_id = self.sale_id.create_bigcommerce_operation('shipment', 'export',
                                                                 self.sale_id.bigcommerce_store_id, 'Processing...',
                                                                 False)
        self._cr.commit()
        try:
            response = request(method="POST", url=api_url, data=json.dumps(request_data), headers=headers)
            _logger.info("Sending Post Request To {}".format(api_url))
            _logger.info("Sending Post Request To {}".format(json.dumps(request_data)))
            if response.status_code in [200, 201]:
                response_data = response.json()
                self.message_post(body="Shipment Created in Bigcommerce : {}".format(response_data.get('id')))
                process_message = "Shipment Created in Bigcommerce : {}".format(response_data.get('id'))
                self.sale_id.create_bigcommerce_operation_detail('order', 'export', False, response_data,
                                                                 operation_id, False, False,
                                                                 process_message)
                self.bigcommerce_shimpment_id = response_data.get('id')
                self.sale_id.bigcommerce_shipment_order_status = 'Shipped'
            else:
                process_message = response.content
                self.sale_id.create_bigcommerce_operation_detail('order', 'export', request_data, False,
                                                                 operation_id, False, True,
                                                                 process_message)
        except Exception as e:
            _logger.info(" Getting an Issue in Export Shipment Response {}".format(e))
            raise ValidationError(e)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Yeah! Successfully Export Order .",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        customer_location_id = self.env.ref('stock.stock_location_customers')
        if self.sale_id.bigcommerce_store_id and self.location_dest_id.id == customer_location_id.id:
            self.export_shipment_to_bigcommerce()
        return res

    def get_order_shipment(self):
        tracking_number = shipping_provider = ''
        shipping_cost = 0.0 
        bigcommerce_store_hash = self.sale_id.bigcommerce_store_id.bigcommerce_store_hash
        bigcommerce_client_seceret  = self.sale_id.bigcommerce_store_id.bigcommerce_x_auth_client
        bigcommerce_x_auth_token = self.sale_id.bigcommerce_store_id.bigcommerce_x_auth_token
        headers = {"Accept": "application/json",
                   "X-Auth-Client": "{}".format(bigcommerce_client_seceret),
                   "X-Auth-Token": "{}".format(bigcommerce_x_auth_token),
                   "Content-Type": "application/json"}
        url = "%s%s/v2/orders/%s/shipments"%(self.sale_id.bigcommerce_store_id.bigcommerce_api_url,bigcommerce_store_hash,self.sale_id.big_commerce_order_id)
        try:
            response = request(method="GET",url=url,headers=headers)
            if response.status_code in [200,201]:
                response = response.json()
                _logger.info("BigCommerce Get Shipment  Response : {0}".format(response))
                for response in response:
                    tracking_number += response.get('tracking_number')
                    shipping_provider += response.get('shipping_provider')
                    shipping_cost += float(response.get('merchant_shipping_cost'))
                    shipment_id = response.get('id')
                self.with_user(1).write({'carrier_price':shipping_cost,'carrier_tracking_ref':tracking_number,'bc_shipping_provider':shipping_provider,'bigcommerce_shimpment_id':shipment_id})
                self.sale_id.with_user(1).bigcommerce_shipment_order_status = 'Shipped'
            else:
                self.with_user(1).message_post(body="Getting an Error in Import Shipment Information : {0}".format(response.content))
        except Exception as e:
            self.with_user(1).message_post(body="Getting an Error in Import Shipment Information : {0}".format(e))
