from odoo import fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
import logging
import requests
import json

_logger = logging.getLogger("BigCommerce")


class ResPartner(models.Model):
    _inherit = "res.partner"
    bigcommerce_store_id = fields.Many2one('bigcommerce.store.configuration', string="Bigcommerce Store", copy=False)
    bigcommerce_customer_id = fields.Char("Bigcommerce Customer ID", copy=False)
    is_available_in_bigcommerce = fields.Boolean(string='Is Exported to BigCommerce', default=False, copy=False)
    bigcommerce_customer_group_id = fields.Many2one('bigcommerce.customer.group', string="Bigcommerce Customer Group")
    bc_companyname = fields.Char(string='BC Company Name')

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
                                            warehouse_id=False, fault_operation=False, customer_message=False):
        bigcommerce_operation_details_obj = self.env['bigcommerce.operation.details']
        vals = {
            'bigcommerce_operation': operation,
            'bigcommerce_operation_type': operation_type,
            'bigcommerce_request_message': '{}'.format(req_data),
            'bigcommerce_response_message': '{}'.format(response_data),
            'operation_id': operation_id.id,
            'warehouse_id': warehouse_id and warehouse_id.id or False,
            'fault_operation': fault_operation,
            'process_message': customer_message
        }
        operation_detail_id = bigcommerce_operation_details_obj.create(vals)
        return operation_detail_id

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
                response_data = bigcommerce_store_id.send_get_request_from_odoo_to_bigcommerce(api_operation)
                if response_data.status_code in [200, 201]:
                    response_data = response_data.json()
                    _logger.info("Customer Response Data : {0}".format(response_data))
                    records = response_data.get('data')

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
                                    'bigcommerce_customer_group_id': customer_group_id.id
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
                                    'bigcommerce_customer_group_id': customer_group_id.id
                                    # 'bigcommerce_customer_id':record.get('id'),
                                    # 'bigcommerce_store_id':bigcommerce_store_id.id
                                }
                                partner_id.write(vals)
                                customer_message = "Customer Data Updated %s" % (partner_id.name)
                                _logger.info("Customer Updated : {0}".format(partner_id.name))
                                req_data = record
                            self.create_bigcommerce_operation_detail('customer', 'import', req_data, response_data,
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

    def add_customer_address(self, partner_id=False, bigcommerce_store_id=False, customer_operation_id=False,
                             warehouse_id=False):
        req_data = False
        customer_process_message = "Process Completed Successfully!"
        if partner_id and partner_id.bigcommerce_customer_id:
            try:
                #prefix = len(bigcommerce_store_id.bc_customer_prefix) + 1
                bc_customer_id = partner_id.bigcommerce_customer_id#[prefix:]
                api_operation = "/v2/customers/%s/addresses" % (bc_customer_id)
                response_data = bigcommerce_store_id.send_get_request_from_odoo_to_bigcommerce(api_operation)
                _logger.info("BigCommerce Get Customer Address Response : {0}".format(response_data))
                _logger.info("Response Status: {0}".format(response_data.status_code))

                if response_data.status_code in [200, 201, 204]:
                    response_data = response_data.json()
                    _logger.info("Customer Response Data : {0}".format(response_data))
                    for record in response_data:
                        partner_id.street = record.get('street_1', "")
                        partner_id.street2 = record.get("street_2", "")
                        partner_id.zip = record.get('zip', "")
                        partner_id.city = record.get('city', "")
                        country_code = record.get("country_iso2", "")
                        country_obj = self.env['res.country'].search(
                            [('code', '=', country_code)], limit=1)
                        partner_id.country_id = country_obj and country_obj.id
                        state_name = record.get('state', "")
                        state_obj = self.env['res.country.state'].search([('name', '=', state_name)], limit=1)
                        partner_id.state_id = state_obj and state_obj.id

                        _logger.info("Customer Address Updated : {0}".format(partner_id.name))
                        response_data = record
                        customer_message = "%s Customer Address Updated" % (partner_id.name)
                        self.create_bigcommerce_operation_detail('customer', 'import', req_data, response_data,
                                                                 customer_operation_id, warehouse_id, False,
                                                                 customer_message)
                        self._cr.commit()
                        break
                    customer_operation_id and customer_operation_id.write(
                        {'bigcommerce_message': customer_process_message})
                    _logger.info("Import Customer Process Completed ")
                else:
                    _logger.info("Getting an Error In Import Customer Address Responase".format(response_data))
                    customer_res_message = response_data.content
                    customer_message = "Getting an Error In Import Customer Address Responase".format(
                        customer_res_message)
                    self.create_bigcommerce_operation_detail('customer', 'import', req_data, customer_res_message,
                                                             customer_operation_id, warehouse_id, True,
                                                             customer_message)
            except Exception as e:
                customer_process_message = "Process Is Not Completed Yet! %s" % (e)
                _logger.info("Getting an Error In Import Customer Address Responase".format(e))
                customer_message = "Getting an Error In Import Customer Adderss Responase".format(e)
                self.create_bigcommerce_operation_detail('customer', 'import', response_data, customer_process_message,
                                                         customer_operation_id, warehouse_id, True, customer_message)
        else:
            self.create_bigcommerce_operation_detail('customer', 'import', False, False,
                                                     customer_operation_id, False, False,
                                                     "For Adderss Import, Not Getting Customer In odoo.")
        customer_operation_id and customer_operation_id.write({'bigcommerce_message': customer_process_message})
        self._cr.commit()

    def export_customer_to_bigcommerce(self,bc_store_ids=False):
        """
        :return: this method export customer to bigcommerce
        """
        for c_partner in self:
            bc_store_ids = bc_store_ids if bc_store_ids else c_partner.bigcommerce_store_id
            if not bc_store_ids:
                raise ValidationError(_("Please select the bigcommerce Store in Customer"))
            for bc_store_id in bc_store_ids:
                address = []
                if not c_partner.name and c_partner.email:
                    raise ValidationError(_('Please enter the name of customer and email address before the export '))

                if c_partner.email:
                    email = c_partner.email and c_partner.email.split('@')[1]
                    partners = self.env['res.partner'].search([])
                    b = [pp for pp in partners if (pp.email and len(pp.email.split('@')) > 1 and pp.email.split('@')[1] == email and email != 'gmail.com' and pp.bigcommerce_customer_id)]
                    if b:
                        raise ValidationError(_("{0} Customer Already There in Bigcommerce With Domain:{1}".format(b[0].name,email)))

                # preparing dict for sending data to bigcommerce
                partner = c_partner.parent_id if c_partner.parent_id else c_partner
                parent_address_data = {
                                "first_name": partner.name,
                                "last_name": " ",
                                "address1": partner.street or '',
                                "city": partner.city or '',
                                "state_or_province": "{}".format(partner.state_id and partner.state_id.name or " "),
                                "postal_code": "{}".format(partner.zip),
                                "country_code": "{}".format(partner.country_id and partner.country_id.code or " "),
                                "phone": partner.mobile or partner.phone or "",
                                "address_type": "residential",
                            }
                address.append(parent_address_data)
                for child_id in partner.child_ids:
                    if not child_id.name:
                        raise ValidationError("Please Enter the Child Customer Name Before Export to Bigcommerce")
                    address.append({
                        "first_name": child_id.name,
                        "last_name": " ",
                        "address1": child_id.street or '',
                        "city": child_id.city or '',
                        "state_or_province": "{}".format(child_id.state_id and child_id.state_id.name or " "),
                        "postal_code": "{}".format(child_id.zip),
                        "country_code": "{}".format(child_id.country_id and child_id.country_id.code or " "),
                        "phone": child_id.mobile or child_id.phone or "",
                        "address_type": "residential"
                    })
                res_partner_data = [
                    {
                        "email": partner.email or '',
                        "first_name": partner.name,
                        "last_name": " ",
                        "company": c_partner.parent_id.name if c_partner.parent_id and c_partner.parent_id.company_type=='company' else '',
                        "phone": "{}".format(c_partner.phone if c_partner.phone else ''),
                        "customer_group_id": int(
                            c_partner.bigcommerce_customer_group_id and c_partner.bigcommerce_customer_group_id.customer_group_id) or None,
                        # "addresses": [
                        #     {
                        #         "first_name": self.name,
                        #         "last_name": " ",
                        #         "address1": self.street or '',
                        #         "city": self.city or '',
                        #         "state_or_province": "{}".format(self.state_id and self.state_id.name or " "),
                        #         "postal_code": "{}".format(self.zip),
                        #         "country_code": "{}".format(self.country_id and self.country_id.code or " "),
                        #         "phone": self.mobile or self.phone,
                        #         "address_type": "residential",
                        #     }
                        # ],
                        "addresses":address,
                        # "authentication": {
                        #     "force_password_reset": False,
                        #     "new_password": "santoro_123"
                        # }
                    }
                ]

                api_url = bc_store_id.bigcommerce_api_url
                store_id = bc_store_id.bigcommerce_store_hash
                url = "%s%s/v3/customers" % (api_url, store_id)
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-Auth-Client': '{}'.format(bc_store_id.bigcommerce_x_auth_client),
                    'X-Auth-Token': "{}".format(bc_store_id.bigcommerce_x_auth_token)
                }
                try:
                    _logger.info(">>> sending post request to {}".format(api_url, headers, ))
                    response_data = requests.post(url=url, headers=headers, data=json.dumps(res_partner_data))
                    if response_data.status_code in [200, 201]:
                        _logger.info(">>>> get successfully response from {}".format(response_data.json()))
                        response_data = response_data.json()
                        for data in response_data.get('data'):
                            customer_id = data.get('id')
                            partner.bigcommerce_customer_id = customer_id
                            partner.is_available_in_bigcommerce = True
                            if partner.child_ids:
                                partner.child_ids.write({'is_available_in_bigcommerce':True})#'bigcommerce_customer_id':customer_id,
                        # return {
                        #     'effect': {
                        #         'fadeout': 'slow',
                        #         'message': "Yeah! successfully export customer  .",
                        #         'img_url': '/web/static/src/img/smile.svg',
                        #         'type': 'rainbow_man',
                        #     }
                        # }
                    else:
                        raise ValidationError(response_data.text)
                except Exception as error:
                    raise ValidationError(error)