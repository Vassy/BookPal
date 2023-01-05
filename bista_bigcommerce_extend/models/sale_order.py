
import json
import logging

from datetime import datetime
from requests import request

from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.addons.sale.models.sale_order import SaleOrder

_logger = logging.getLogger("BigCommerce")


class SaleOrderVts(models.Model):
    _inherit = "sale.order"

    # bc_tax_total = fields.Float('BC Tax', compute="_get_cal_bc_tax")

    # def _get_cal_bc_tax(self):
    #     for order in self:
    #         order.bc_tax_total = sum(
    #             order.order_line.mapped('big_commerce_tax'))

    def action_redirect_to_payment_transaction(self):
        action = self.env.ref('account.action_account_payments').read()[0]
        action['domain'] = [('id', 'in', self.account_payment_ids.ids)]
        return action


    def get_coupon_response_data(self, order_data, bigcommerce_store_id):
        """Method return coupon api respons."""
        api_url = order_data.get('coupons').get('url')
        auth_token = bigcommerce_store_id.bigcommerce_x_auth_token
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'X-Auth-Token': "{}".format(auth_token)
        }
        try:
            api_response = request(
                method="GET", headers=headers, url=api_url)
            if api_response.status_code in [200, 201]:
                _logger.info(
                    ">>> get successfully response from {}".format(
                        api_url))
                coupon_data = api_response.json()
                return coupon_data
            else:
                _logger.info(
                    ">>>> this order number does not have any coupon  ")
                return None
        except Exception as e:
            _logger.info(e)

    def create_sales_order_from_bigcommerce(self, vals):
        """Create sales order form big commerce."""
        sale_order = self.env['sale.order']
        fpos = False
        order_vals = {
            'company_id': vals.get('company_id'),
            'partner_id': vals.get('partner_id'),
            'partner_invoice_id': vals.get('partner_invoice_id'),
            'partner_shipping_id': vals.get('partner_shipping_id'),
            'warehouse_id': vals.get('warehouse_id'),
        }
        new_record = sale_order.new(order_vals)
        new_record.onchange_partner_id()
        order_vals = sale_order._convert_to_write(
            {name: new_record[name] for name in new_record._cache})
        new_record = sale_order.new(order_vals)
        new_record.with_context(with_company=vals.get(
            'company_id')).onchange_partner_shipping_id()
        order_vals = sale_order._convert_to_write(
            {name: new_record[name] for name in new_record._cache})
        fpos = order_vals.get('fiscal_position_id', fpos)
        if not fpos:
            fpos = self.env['account.fiscal.position'].with_context(
                with_company=vals.get(
                    'company_id')).get_fiscal_position(
                vals.get('partner_id'), vals.get('partner_id'))
        order_vals.update({
            'company_id': vals.get('company_id'),
            'picking_policy': 'direct',
            'partner_invoice_id': vals.get('partner_invoice_id'),
            'partner_shipping_id': vals.get('partner_shipping_id'),
            'partner_id': vals.get('partner_id'),
            'date_order': vals.get('date_order', ''),
            'state': 'draft',
            'carrier_id': vals.get('carrier_id', ''),
            'currency_id': vals.get('currency_id', False),
            'pricelist_id': vals.get('pricelist_id'),
            'note': vals.get('customer_message', ''),
            # Unset fiscal position to avoid recalculation of Avatax
            'fiscal_position_id': False,
            'note': vals.get('customer_message', '')
        })
        return order_vals

    def create_sale_order_line_from_bigcommerce(self, vals):
        """Create sale order line from big commrce."""
        sale_order_line = self.env['sale.order.line']
        order_line = {
            'order_id': vals.get('order_id'),
            'product_id': vals.get('product_id', ''),
            'company_id': vals.get('company_id', ''),
            'name': vals.get('description'),
            'product_uom': vals.get('product_uom')
        }
        new_order_line = sale_order_line.new(order_line)
        new_order_line.product_id_change()
        order_line = sale_order_line._convert_to_write(
            {name: new_order_line[name] for name in new_order_line._cache})
        order_line.update({
            'order_id': vals.get('order_id'),
            'product_uom_qty': vals.get('order_qty', 0.0),
            'price_unit': vals.get('price_unit', 0.0),
            'discount': vals.get('discount', 0.0),
            'state': 'draft',
        })
        if float(vals.get('big_commerce_tax')) <= 0.0:
            order_line.update({
                'tax_id': False
            })
        return order_line

    def create_bigcommerce_operation(
            self, operation, operation_type,
            bigcommerce_store_id, log_message, warehouse_id):
        """Create BC operation."""
        vals = {
            'bigcommerce_operation': operation,
            'bigcommerce_operation_type': operation_type,
            'bigcommerce_store': bigcommerce_store_id and
            bigcommerce_store_id.id,
            'bigcommerce_message': log_message,
            'warehouse_id': warehouse_id and warehouse_id.id or False
        }
        operation_id = self.env['bigcommerce.operation'].create(vals)
        return operation_id

    def create_bigcommerce_operation_detail(
            self, operation, operation_type, req_data,
            response_data, operation_id,
            warehouse_id=False, fault_operation=False,
            process_message=False):
        """Create BC operation detail."""
        bigcommerce_operation_details_obj = \
            self.env['bigcommerce.operation.details']
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

    def bigcommerce_shipping_address_api_method(
            self, order=False, bigcommerce_store_id=False):
        """Bigcommerce shipping_address api_method."""
        api_url = order.get('shipping_addresses').get('url')
        auth_token = bigcommerce_store_id and \
            bigcommerce_store_id.bigcommerce_x_auth_token
        try:
            if api_url:
                headers = {"Accept": "application/json",
                           "X-Auth-Token": auth_token,
                           "Content-Type": "application/json"}
                response_data = request(
                    method="GET", headers=headers, url=api_url)
                if response_data.status_code in [200, 201]:
                    _logger.info(
                        ">>>>> Get Successfully Response From {}".format(
                            api_url))
                    response_data = response_data.json()
                    for data in response_data:
                        return data
            else:
                _logger.info(">>>>> api url not found in response ")
                return None
        except Exception as error:
            _logger.info(">>>>> Getting an Error {}".format(error))

    def create_discount_line(self, order, order_id):
        """If discount amount there then create discount line."""
        if float(order.get('discount_amount', '0')) > 0:
            discount_product_id = self.env.ref(
                'bigcommerce_odoo_integration.'
                'product_product_bigcommerce_discount')
            self.env['sale.order.line'].sudo().\
                create({
                    'product_id': discount_product_id.id,
                    'price_unit': -float(
                        order.get('discount_amount')),
                    'product_uom_qty': 1.0,
                    'state': 'draft',
                    'order_id': order_id.id,
                    'company_id': order_id.company_id.id})

    def create_product_order_line(
            self, order, bigcommerce_store_id, order_id,
            operation_id, warehouse_id, req_data):
        """Create order line for product."""
        try:
            product_details = "/v2{0}".format(
                order.get('products').get('resource'))
            response_data = bigcommerce_store_id.\
                send_get_request_from_odoo_to_bigcommerce(
                    product_details)
            if response_data.status_code in [200, 201, 204]:
                response_data = response_data.json()
                if response_data and order_id:
                    self.prepare_sale_order_lines(
                        order_id, response_data,
                        operation_id, warehouse_id, order,
                        bigcommerce_store_id)
                else:
                    product_message = "Product Is not available in order " + \
                        ": {0}!".format(
                            order_id and order_id.name)
                    self.create_bigcommerce_operation_detail(
                        'order', 'import', req_data, response_data,
                        operation_id, warehouse_id, True,
                        product_message)
                if float(order.get('total_tax', '0.0')) > 0:
                    vat_product_id = self.env.ref(
                        'bigcommerce_odoo_integration.'
                        'product_product_bigcommerce_tax')
                    taxline_vals = {
                        'product_id': vat_product_id.id,
                        'price_unit': float(order.get('total_tax', 0.0)),
                        'product_uom_qty': 1,
                        'order_id': order_id.id, 'name': vat_product_id.name,
                        'company_id': self.env.user.company_id.id
                    }
                    line_id = self.env['sale.order.line'].sudo().create(
                        taxline_vals)
                    _logger.info("Tax Line Vals : {0},Line ID :{1}".format(
                        taxline_vals, line_id))
                order_id.sudo()._amount_all()
                if order.get('payment_status') in ["captured", "paid"]:
                    #     # order_id.action_confirm()
                    order_id.get_order_transaction(through_order_cron=True)
                # if len(order_id.order_line) > 0:
                #     order_id.action_confirm()
                self._cr.commit()
        except Exception as e:
            _logger.info(
                "Getting an Error In Import Order Line Response {}".format(e))
            process_message = "Getting an Error In Import Order" + \
                " Response {}".format(
                    e, order_id and order_id.name)
            self.create_bigcommerce_operation_detail(
                'order', 'import', '', '',
                operation_id,
                warehouse_id, True,
                process_message)

    def bigcommerce_to_odoo_import_orders(
            self, warehouse_id=False, bigcommerce_store_ids=False,
            last_modification_date=False, today_date=False, total_pages=20,
            bigcommerce_order_status=False):
        """Big commerce to odoo import order."""
        for bigcommerce_store_id in bigcommerce_store_ids:
            req_data = False
            process_message = "Process Completed Successfully!"
            operation_id = self.create_bigcommerce_operation(
                'order', 'import', bigcommerce_store_id,
                'Processing...', warehouse_id)
            self._cr.commit()
            late_modification_date_flag = False
            try:
                last_modification_date = last_modification_date if \
                    last_modification_date else \
                    bigcommerce_store_id.from_order_date
                last_date = last_modification_date.strftime("%Y-%m-%d")
                last_time = last_modification_date.strftime("%H:%M:%S")
                today_date = today_date if today_date else \
                    bigcommerce_store_id.last_modification_date
                diff = today_date - last_modification_date
                total_pages = total_pages if total_pages else \
                    (diff.days * 2)
                todaydate = today_date.strftime("%Y-%m-%d")
                todaytime = today_date.strftime("%H:%M:%S")
                last_modification_date = last_date + " " + last_time
                today_date = todaydate + " " + todaytime
                for page_no in range(1, total_pages):
                    api_operation = "/v2/orders?max_date_created="\
                        "{0}&min_date_created={1}&status_id={2}&page={3}"\
                        "&limit={4}".format(
                            today_date,
                            last_modification_date,
                            bigcommerce_order_status,
                            page_no,
                            250)
                    # api_operation = "/v2/orders?max_date_created="\
                    #     "{0}&min_date_created={1}&page={2}&limit={3}"\
                    #     .format(
                    #         today_date, last_modification_date,
                    #         page_no, 250)
                    response_data = bigcommerce_store_id.\
                        send_get_request_from_odoo_to_bigcommerce(
                            api_operation)
                    if response_data.status_code in [200, 201]:
                        response_data = response_data.json()
                        _logger.info(
                            "Order Response Data : {0}".format(
                                response_data))
                        for order in response_data:
                            if order.get('status') == 'Pending' or \
                                    order.get('status') == 'Cancelled' or \
                                    order.get('status') == 'Incomplete':
                                continue
                            big_commerce_order_id = order.get('id')
                            sale_order = self.env['sale.order'].search(
                                [('big_commerce_order_id',
                                  '=',
                                  big_commerce_order_id)])
                            if not sale_order:
                                partner_parent_id = False
                                shipping_address_api_respons = \
                                    self.bigcommerce_shipping_address_api_method(
                                        order, bigcommerce_store_id)
                                date_time_str = order.get('orderDate')
                                customerEmail = order.get(
                                    'billing_address').get('email')
                                company_name = order.get(
                                    'billing_address').get('company')
                                city = order.get('billing_address').get('city')
                                first_name = order.get(
                                    'billing_address').get('first_name')
                                last_name = order.get(
                                    'billing_address').get('last_name')
                                country_iso2 = order.get(
                                    'billing_address').get('country_iso2')
                                street = order.get(
                                    'billing_address').get('street_1', '')
                                street_2 = order.get(
                                    'billing_address').get('street_2', '')
                                country_obj = self.env['res.country'].search(
                                    [('code', '=', country_iso2)], limit=1)
                                state_obj = self.env['res.country.state'].\
                                    search(
                                    [('name', '=',
                                      order.get('billing_address').get(
                                          'state'))], limit=1)

                                phone = order.get(
                                    'billing_address').get('phone')
                                zip = order.get('billing_address').get('zip')

                                total_tax = order.get('total_tax')
                                customerId = bigcommerce_store_id.\
                                    bc_customer_prefix + \
                                    "_" + str(order.get('customer_id'))
                                carrier_id = self.env['delivery.carrier'].\
                                    search(
                                    [('is_bigcommerce_shipping_method',
                                      '=', True)], limit=1)
                                partner_obj = self.env['res.partner'].search(
                                    [('bigcommerce_customer_id', '=',
                                      customerId)], limit=1)
                                partner_vals = {
                                    'phone': phone,
                                    'zip': zip,
                                    'city': city,
                                    'country_id': country_obj and
                                    country_obj.id,
                                    'email': customerEmail,
                                    'is_available_in_bigcommerce': True,
                                    'bigcommerce_store_id':
                                    bigcommerce_store_id.id,
                                    'street': street,
                                    'street2': street_2,
                                    'state_id': state_obj and state_obj.id
                                }
                                if company_name and not \
                                    self.env['res.partner'].search(
                                        [('company_type', '=', 'company'),
                                         ('email', '=', customerEmail)],
                                        limit=1):
                                    company_vals = {
                                        'company_type': 'company',
                                        'name': company_name}
                                    partner_parent_id = \
                                        self.env['res.partner'].create(
                                            {**partner_vals, **company_vals})
                                if customerId == 0:
                                    partner_vals.update({
                                        'name': "%s %s (Guest)" % (
                                            first_name, last_name),
                                        'bigcommerce_customer_id':
                                        bigcommerce_store_id.
                                        bc_customer_prefix +
                                        str(big_commerce_order_id),
                                        'parent_id': partner_parent_id and
                                        partner_parent_id.id
                                    })
                                    partner_obj = self.env['res.partner'].\
                                        create(partner_vals)
                                if not partner_obj:
                                    partner_vals.update({
                                        'name': "%s %s" % (
                                            first_name, last_name),
                                        'bigcommerce_customer_id': customerId,
                                        'parent_id': partner_parent_id and
                                        partner_parent_id.id
                                    })
                                    partner_obj = self.env['res.partner'].create(
                                        partner_vals)
                                if not partner_obj:
                                    process_message = \
                                        "Customer is not exist in Odoo {}".\
                                        format(customerId)
                                    self.create_bigcommerce_operation_detail(
                                        'order', 'import', req_data,
                                        response_data,
                                        operation_id, warehouse_id, True,
                                        process_message)
                                    late_modification_date_flag = True
                                    continue
                                shipping_partner_state = \
                                    shipping_address_api_respons.get(
                                        'state') or ''  # change the state
                                shipping_partner_country = \
                                    shipping_address_api_respons.get(
                                        'country') or ''  # chnage the country
                                state_id = self.env['res.country.state'].\
                                    search(
                                        [('name', '=',
                                          shipping_partner_state)],
                                        limit=1)
                                country_id = self.env['res.country'].search(
                                    [('name', '=',
                                      shipping_partner_country)],
                                    limit=1)
                                # add address field heare
                                shipping_partner_first_name = \
                                    shipping_address_api_respons.get(
                                        'first_name')
                                shipping_partner_last_name = \
                                    shipping_address_api_respons.get(
                                        'last_name')
                                shipping_partner_company = \
                                    shipping_address_api_respons.get(
                                        'company')
                                shipping_partner_name = "%s %s" % (
                                    shipping_partner_first_name,
                                    shipping_partner_last_name)
                                shipping_partner_street_1 = \
                                    shipping_address_api_respons.get(
                                        'street_1')
                                shipping_partner_street_2 = \
                                    shipping_address_api_respons.get(
                                        'street_2')
                                shipping_partner_city = \
                                    shipping_address_api_respons.get(
                                        'city')
                                shipping_partner_zip = \
                                    shipping_address_api_respons.get(
                                        'zip')
                                shipping_partner_email = \
                                    shipping_address_api_respons.get(
                                        'email')
                                shipping_partner_phone = \
                                    shipping_address_api_respons.get(
                                        'phone')

                                partner_shipping_id = self.\
                                    env['res.partner'].sudo().search(
                                        [('street', '=',
                                          shipping_partner_street_1),
                                         ('zip', '=', shipping_partner_zip),
                                         ('email', '=',
                                          shipping_partner_email),
                                         ('country_id', '=', country_id.id)],
                                        limit=1)
                                if not partner_shipping_id:
                                    _logger.info(">>> creating new partner ")
                                    res_partner_vals = {
                                        'name': shipping_partner_name,
                                        'bc_companyname':
                                        shipping_partner_company,
                                        'phone': shipping_partner_phone,
                                        'email': shipping_partner_email,
                                        'street': shipping_partner_street_1,
                                        'street2': shipping_partner_street_2,
                                        'city': shipping_partner_city,
                                        'zip': shipping_partner_zip,
                                        'state_id': state_id.id,
                                        'type': 'delivery',
                                        'parent_id':
                                        partner_parent_id.id if
                                        partner_parent_id else partner_obj.id,
                                        'country_id': country_id.id
                                    }
                                    partner_shipping_id = \
                                        self.env['res.partner'].sudo().create(
                                            res_partner_vals)
                                    _logger.info(
                                        ">>> successfully create shipping"
                                        " partner {}".format(
                                            shipping_partner_first_name))
                                    self._cr.commit()
                                pricelist_id = self.env['product.pricelist'].\
                                    search([('currency_id.name',
                                             '=',
                                             order.get('currency_code'))],
                                           limit=1)
                                if not pricelist_id:
                                    pricelist_id = bigcommerce_store_id.\
                                        pricelist_id
                                _logger.info(
                                    "Currency Code >>> {0} >>> "
                                    "Pricelist >>> {1}".format(
                                        order.get('currency_code'),
                                        pricelist_id))
                                vals = {}
                                base_shipping_cost = \
                                    shipping_address_api_respons.get(
                                        'base_cost', 0.0)
                                currency_id = self.env['res.currency'].search(
                                    [('name', '=',
                                      order.get('currency_code'))], limit=1)

                                vals.update({
                                    'partner_id': partner_parent_id.id if
                                    partner_parent_id else partner_obj.id,
                                    'partner_invoice_id': partner_obj.id,
                                    'partner_shipping_id':
                                    partner_shipping_id.id,
                                    # chnage value shipping_id
                                    'date_order': date_time_str or today_date,
                                    'bc_order_date': date_time_str or
                                    today_date,
                                    'carrier_id': carrier_id and carrier_id.id,
                                    'company_id': warehouse_id.company_id and
                                    warehouse_id.company_id.id or
                                    self.env.user.company_id.id,
                                    'warehouse_id': warehouse_id.id,
                                    'carrierCode': '',
                                    'serviceCode': '',
                                    'currency_id': currency_id.id,
                                    'delivery_price': base_shipping_cost,
                                    'pricelist_id':
                                    partner_obj.property_product_pricelist.id
                                    if partner_obj.property_product_pricelist
                                    else pricelist_id.id,
                                    'customer_message': order.get(
                                        'customer_message', ''),
                                    'amount_tax': total_tax
                                })
                                order_vals = \
                                    self.create_sales_order_from_bigcommerce(
                                        vals)
                                order_vals.update(
                                    {'big_commerce_order_id':
                                     big_commerce_order_id,
                                     'bigcommerce_store_id':
                                     bigcommerce_store_id.id,
                                     'payment_status': 'paid' if
                                     order.get('payment_status') in
                                     ["captured", "paid"]
                                     else 'not_paid',
                                     'payment_method':
                                     order.get('payment_method'),
                                     'bigcommerce_shipment_order_status':
                                     order.get('status')
                                     })
                                order_id = self.create(order_vals)
                                self.create_product_order_line(
                                    order, bigcommerce_store_id,
                                    order_id, operation_id, warehouse_id,
                                    req_data)
                                if carrier_id and order_id:
                                    order_id.set_delivery_line(
                                        carrier_id, base_shipping_cost)
                                try:
                                    self.create_discount_line(order, order_id)
                                except Exception as e:
                                    process_message = \
                                        "Getting an Error In Create Order"\
                                        " procecss {}"\
                                        .format(e)
                                    self.create_bigcommerce_operation_detail(
                                        'order', 'import', '', '',
                                        operation_id,
                                        warehouse_id, True, process_message)
                                    late_modification_date_flag = True
                                    continue
                                process_message = "Sale Order Created {0}".\
                                    format(order_id and order_id.name)
                                _logger.info("Sale Order Created {0}".format(
                                    order_id and order_id.name))
                                order_id.message_post(
                                    body="Order Successfully Import From "
                                    "Bigcommerce")
                                self.create_bigcommerce_operation_detail(
                                    'order', 'import', req_data, response_data,
                                    operation_id, warehouse_id, False,
                                    process_message)
                            else:
                                process_message = "Order Already in Odoo {}".\
                                    format(sale_order and sale_order.name)
                                self.create_bigcommerce_operation_detail(
                                    'order', 'import', req_data, response_data,
                                    operation_id, warehouse_id, True,
                                    process_message)
                                self._cr.commit()
                        if not late_modification_date_flag:
                            current_date = datetime.now()
                            bigcommerce_store_id.last_modification_date = \
                                current_date
            except Exception as e:
                _logger.info(
                    "Getting an Error In Import Order Response {}".format(e))
                process_message = "Getting an Error In Import Order"\
                    " Response {}".format(e)
                self.create_bigcommerce_operation_detail(
                    'order', 'import', '', '', operation_id, warehouse_id,
                    True, process_message)
            operation_id and operation_id.write(
                {'bigcommerce_message': process_message})
            if len(operation_id.operation_ids) <= 0:
                operation_id.sudo().unlink()
            bigcommerce_store_ids.bigcommerce_operation_message = \
                " Import Sale Order Process Complete "

    def prepare_sale_order_lines(
            self, order_id=False, product_details=False,
            operation_id=False, warehouse_id=False, order_data=False,
            bigcommerce_store_id=False):
        """Prepare sale order line."""
        for order_line in product_details:
            product_bigcommerce_id = order_line.get('product_id')
            listing_id = self.env['bc.store.listing'].search(
                [('bigcommerce_store_id', '=', bigcommerce_store_id.id),
                 ('bc_product_id', '=', product_bigcommerce_id)], limit=1)
            product_id = listing_id.product_tmpl_id.product_variant_id
            if listing_id.listing_item_ids:
                listing_item_id = listing_id.listing_item_ids.filtered(
                    lambda line: line.bc_product_id == str(
                        order_line.get('variant_id')) and
                    line.bigcommerce_store_id.id == bigcommerce_store_id.id)
                product_id = listing_item_id.product_id
            if not product_id:
                response_msg = "Sale Order : {0} Prouduct Not Found Product"\
                    " SKU And Name : {1}".format(
                        order_id and order_id.name, product_bigcommerce_id)
                self.create_bigcommerce_operation_detail(
                    'order', 'import', '', '',
                    operation_id, warehouse_id, True, response_msg)
                continue
            quantity = order_line.get('quantity')
            price = order_line.get('base_price')
            total_tax = order_line.get('total_tax')
            vals = {'product_id': product_id.id,
                    'price_unit': price, 'order_qty': quantity,
                    'order_id': order_id and order_id.id,
                    'description': product_bigcommerce_id,
                    'company_id': self.env.user.company_id.id,
                    'big_commerce_tax': total_tax}
            order_line = self.create_sale_order_line_from_bigcommerce(vals)
            order_line = self.env['sale.order.line'].create(order_line)
            if order_line:
                order_line.big_commerce_tax = total_tax
            _logger.info("Sale Order line Created".format(
                order_line and order_line.product_id and
                order_line.product_id.name))
            response_msg = "Sale Order line Created For Order  : {0}".format(
                order_id.name)
            self.create_bigcommerce_operation_detail(
                'order', 'import', '', '', operation_id,
                warehouse_id, False, response_msg)
        coupon_sale_order = self.get_coupon_response_data(
            order_data, bigcommerce_store_id)
        if coupon_sale_order:
            _logger.info(">>>> update the order line")
            coupon_product = self.env.ref(
                'bigcommerce_odoo_integration.'
                'add_bigcommerce_coupon_as_product')
            for data in coupon_sale_order:
                coupon_vals = {
                    'product_id': coupon_product.id,
                    'price_unit': -(float(data.get('discount', 0.00))),
                    'name': "{}".format(data.get('code')),
                    'product_uom_qty': 1,
                    'order_id': order_id and order_id.id,
                    'company_id': self.env.user.company_id.id
                }
                self.env['sale.order.line'].create(coupon_vals)
                response_msg = "Coupon Sale Order line"\
                    " Created For Order  : {0}".format(
                        coupon_product.name)
                self.create_bigcommerce_operation_detail(
                    'order', 'import', '', data, operation_id,
                    warehouse_id, False, response_msg)
        self._cr.commit()
