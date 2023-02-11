
import logging
from odoo import models
from odoo.addons.bigcommerce_odoo_integration.models.res_partner import \
    ResPartner as BCResPartner

_logger = logging.getLogger("BigCommerce")


class ResPartner(models.Model):
    _inherit = "res.partner"

    def bigcommerce_to_odoo_import_customers(self, warehouse_id=False, bigcommerce_store_ids=False,source_page=1,destination_page=1):
        for bigcommerce_store_id in bigcommerce_store_ids:
            req_data = False
            customer_response_pages = []
            customer_process_message = "Process Completed Successfully!"
            customer_operation_id = self.env['bigcommerce.operation']
            if not customer_operation_id:
                customer_operation_id = self.create_bigcommerce_operation('customer', 'import', bigcommerce_store_id,
                                                                          'Processing...', warehouse_id)
            self._cr.commit()
            try:
                api_operation = "/v3/customers"
                if self._context.get('customer_id'):
                    api_operation = "/v2/customers/{}".format(self._context.get(
                        'customer_id'))
                response_data = bigcommerce_store_id.send_get_request_from_odoo_to_bigcommerce(api_operation)
                if response_data.status_code in [200, 201]:
                    response_data = response_data.json()
                    _logger.info("Customer Response Data : {0}".format(response_data))
                    records = response_data.get('data')
                    total_pages = 0
                    if not self._context.get('customer_id'):
                        total_pages = response_data.get('meta').get('pagination').get('total_pages')
                    if total_pages > 0:
                        bc_total_pages = total_pages + 1
                        inp_from_page = source_page or bigcommerce_store_id.source_of_import_data
                        inp_total_pages = destination_page or bigcommerce_store_id.destination_of_import_data
                        from_page = bc_total_pages - inp_total_pages
                        total_pages = bc_total_pages - inp_from_page
                    else:
                        from_page = source_page or bigcommerce_store_id.source_of_import_data
                        total_pages = destination_page or bigcommerce_store_id.destination_of_import_data
                    if total_pages > 1:
                        while (total_pages >= from_page):
                                try:
                                    page_api = "/v3/customers?page=%s" % (total_pages)
                                    page_response_data = bigcommerce_store_id.send_get_request_from_odoo_to_bigcommerce(
                                        page_api)
                                    if page_response_data.status_code in [200, 201]:
                                        page_response_data = page_response_data.json()
                                        _logger.info("Customer Response Data : {0}".format(page_response_data))
                                        page_records = page_response_data.get('data')
                                        customer_response_pages.append(page_records)
                                except Exception as e:
                                    category_process_message = "Page is not imported! %s" % (e)
                                    _logger.info("Getting an Error In Customer Response {}".format(e))
                                    process_message = "Getting an Error In Import Customer Response {}".format(e)
                                    self.create_bigcommerce_operation_detail('customer', 'import', page_response_data,
                                                                             category_process_message,
                                                                             customer_operation_id, warehouse_id, True,
                                                                             process_message)
                                total_pages = total_pages - 1
                    else:
                        customer_response_pages.append(records)
                    if self._context.get('customer_id'):
                        customer_response_pages = [[response_data]]
                    for customer_response_page in customer_response_pages:
                        for record in customer_response_page:
                            bc_customer_id = str(record.get('id', False))#bigcommerce_store_id.bc_customer_prefix + "_" +
                            partner_id = self.env['res.partner'].search(
                                [('bigcommerce_customer_id', '=', bc_customer_id)], limit=1)
                            customer_group_id = self.env['bigcommerce.customer.group'].search(
                                [('customer_group_id', '=', record.get('customer_group_id')),
                                 ('bc_store_id', '=', bigcommerce_store_id.id)], limit=1)
                            if not partner_id:
                                partner_vals = {
                                    'name': "%s %s" % (record.get('first_name'), record.get('last_name')),
                                    'phone': record.get('phone', ''),
                                    'email': record.get('email'),
                                    'bigcommerce_customer_id': bc_customer_id,
                                    'is_available_in_bigcommerce': True,
                                    'bigcommerce_store_id': bigcommerce_store_id.id,
                                    'bigcommerce_customer_group_id': customer_group_id.id,
                                    'tax_exempt_category':record.get('tax_exempt_category', False)
                                }
                                partner_id = self.env['res.partner'].create(partner_vals)
                                _logger.info("Customer Created : {0}".format(partner_id.name))
                                response_data = record
                                customer_message = "%s Customer Created" % (partner_id.name)
                            else:
                                vals = {
                                    'name': "%s %s" % (record.get('first_name'), record.get('last_name')),
                                    'phone': record.get('phone', ''),
                                    'email': record.get('email'),
                                    'bigcommerce_customer_group_id': customer_group_id.id,
                                    'tax_exempt_category': record.get('tax_exempt_category', False)
                                    # 'bigcommerce_customer_id':record.get('id'),
                                    # 'bigcommerce_store_id':bigcommerce_store_id.id
                                }
                                partner_id.write(vals)
                                customer_message = "Customer Data Updated %s" % (partner_id.name)
                                _logger.info("Customer Updated : {0}".format(partner_id.name))
                                req_data = record
                            operation = 'import'
                            if self._context.get('customer_id'):
                                operation = "update"
                            self.create_bigcommerce_operation_detail('customer', operation, req_data, response_data,
                                                                     customer_operation_id, warehouse_id, False,
                                                                     customer_message)
                            self._cr.commit()
                            try:
                                self.add_customer_address(partner_id, bigcommerce_store_id, customer_operation_id,
                                                          warehouse_id)
                            except Exception as e:
                                continue
                    _logger.info("Import Customer Process Completed ")
                else:
                    _logger.info("Getting an Error In Import Customer Response".format(response_data))
                    customer_res_message = response_data.content
                    customer_message = "Getting an Error In Import Customer Response".format(customer_res_message)
                    self.create_bigcommerce_operation_detail('customer', 'import', req_data, customer_res_message,
                                                             customer_operation_id, warehouse_id, True,
                                                             customer_message)
            except Exception as e:
                customer_process_message = "Process Is Not Completed Yet! %s" % (e)
                _logger.info("Getting an Error In Import Customer Responase".format(e))
                customer_message = "Getting an Error In Import Customer Responase : {0}".format(e)
                self.create_bigcommerce_operation_detail('customer', 'import', response_data, customer_process_message,
                                                         customer_operation_id, warehouse_id, True, customer_message)
            customer_operation_id and customer_operation_id.write({'bigcommerce_message': customer_process_message})
            bigcommerce_store_id.bigcommerce_operation_message = "Import Customer Process Completed."
            self._cr.commit()

    BCResPartner.bigcommerce_to_odoo_import_customers = bigcommerce_to_odoo_import_customers
