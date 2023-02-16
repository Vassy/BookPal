
import logging

from odoo import fields, models
_logger = logging.getLogger("BigCommerce")


class UpdatePartnerWiz(models.TransientModel):
    _name = "update.partner.wiz"
    _description = "Update partner from BC"

    partner_ids = fields.Many2many(
        'res.partner', string="Customers",
        domain="[('bigcommerce_customer_id', '!=', False)]",
        default=lambda self: self._context.get('active_ids'))
    bigcommerce_store_ids = fields.Many2many(
        'bigcommerce.store.configuration',
        string="Bigcommerce Store", copy=False)

    def update_partner(self):
        """Update partner from bc."""
        for partner in self.partner_ids.filtered(
                lambda x: x.bigcommerce_customer_id):
            for store in self.bigcommerce_store_ids:
                customer_process_message = "Process Completed Successfully!"
                api_operation = "/v2/customers/{}".format(
                    partner.bigcommerce_customer_id)
                customer_operation_id = partner.create_bigcommerce_operation(
                    'customer', 'update', store,
                    'Processing...', False)
                response_data = store.\
                    send_get_request_from_odoo_to_bigcommerce(
                        api_operation)
                if response_data.status_code in [200, 201]:
                    response_data = response_data.json()
                    _logger.info(
                        "Customer Response Data : {0}".format(response_data))
                    partner.create_update_cutomer_to_odoo(
                        response_data, store,
                        customer_operation_id, False)
                    customer_operation_id and customer_operation_id.write(
                        {'bigcommerce_message': customer_process_message})
                # customer_operation_id.write({'bigcommerce_message':
                #                              'Process Completed Successfully'})
