from odoo import fields, models, api, _
import logging
import time
_logger = logging.getLogger("BigCommerce")

class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    priceing_rule_id = fields.Char(string='Priceing Rule')

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    is_bigcommerce_pricelist  = fields.Boolean(string='Is Bigcommerce Pricelist?')
    bc_store_id = fields.Many2one('bigcommerce.store.configuration',string='Bigcommerce Store')

    # def bigcommerce_to_odoo_import_pricelist(self,store_ids):
    #     for bigcommerce_store_id in store_ids:
    #         req_data = False
    #         process_message = "Process Completed Successfully!"
    #         operation_id = self.create_bigcommerce_operation('order', 'import', bigcommerce_store_id, 'Processing...',
    #                                                          bigcommerce_store_id.warehouse_id)
    #         self._cr.commit()
    #         late_modification_date_flag = False
    #         try:
    #             pricelist_obj = self.env['product.pricelist']
    #             pricelist_id = pricelist_obj.search([('is_bigcommerce_pricelist', '=', True)])
    #             if not pricelist_id:
    #                 pricelist_id = pricelist_obj.create(
    #                     {'bc_store_id': bigcommerce_store_id.id, 'is_bigcommerce_pricelist': True,
    #                      'name': 'Bigcommerce PriceList'})
    #
    #             # api_operation = "/v3/pricelists"
    #             # response_data = bigcommerce_store_id.send_get_request_from_odoo_to_bigcommerce(api_operation)
    #             # if response_data.status_code in [200, 201]:
    #             #     response_data = response_data.json()
    #             #     _logger.info("Pricelist Response Data : {0}".format(response_data))
    #             #     total_pages = response_data.get('meta').get('pagination').get('total')
    #             # for page_no in total_pages:
    #             #     api_operation = "/v3/pricelists?page={1}".format(page_no)
    #             #     response_data = bigcommerce_store_id.send_get_request_from_odoo_to_bigcommerce(api_operation)
    #             #     if response_data.status_code in [200, 201]:
    #             #         response_data = response_data.json()
    #             #         _logger.info("Pricelist Response Data : {0}".format(response_data))
    #             #         pricelist_obj = self.env['product.pricelist']
    #             #         for pricelist_data in response_data:
    #             #             pricelist_id = pricelist_obj.search([('is_bigcommerce_pricelist', '=', True)])
    #             #             if not pricelist_id:
    #             #                 pricelist_id = pricelist_obj.create({'bc_store_id':bigcommerce_store_id.id,'is_bigcommerce_pricelist':True,'name':'Bigcommerce PriceList'})
    #             #             pricelist_record_api_operation = '/v3/pricelists/{}/records'.format(pricelist_id.bc_pricelist_id)
    #             #             pricelist_record_response_data = bigcommerce_store_id.send_get_request_from_odoo_to_bigcommerce(pricelist_record_api_operation)
    #             #             if pricelist_record_response_data.status_code in [200, 201]:
    #             #                 pricelist_record_response_data = pricelist_record_response_data.json()
    #             #                 _logger.info("Pricelist Response Data : {0}".format(pricelist_record_response_data))
    #             #                 total_item_pages = pricelist_record_response_data.get('meta').get('pagination').get('total')
    #             #                 for page_no in total_item_pages:
    #             #                     api_operation = "/v3/pricelists/{0}/records?page={1}".format(pricelist_id.bc_pricelist_id,page_no)
    #             #                     response_data = bigcommerce_store_id.send_get_request_from_odoo_to_bigcommerce(
    #             #                         api_operation)
    #             #                     if response_data.status_code in [200, 201]:
    #             #                         response_data = response_data.json()
    #             #                         _logger.info("Pricelist Response Data : {0}".format(response_data))
    #             #                         pricelist_item_obj = self.env['product.pricelist.item']
    #             #                         for pricelist_data in response_data:
    #             #                             pricelist_id = pricelist_item_obj.search(
    #             #                                 [('bc_pricelist_id', '=', pricelist_data.get('id'))])
    #             #                             if not pricelist_id:
    #             #                                 pricelist_id = pricelist_obj.create(
    #             #                                     {'bc_pricelist_id': pricelist_data.get('id'),
    #             #                                      'bc_store_id': bigcommerce_store_id.id,
    #             #                                      'is_bigcommerce_pricelist': True,
    #             #                                      'name': pricelist_data.get('name')})
    #
    #         except Exception as e:
    #             _logger.info("Getting an Error In Import Pricelist Response {}".format(e))
    #             process_message = "Getting an Error In Import Pricelist Response {}".format(e)
    #             self.create_bigcommerce_operation_detail('product', 'import', '', '', operation_id, bigcommerce_store_id.warehouse_id, True,
    #                                                      process_message)
    #         operation_id and operation_id.write({'bigcommerce_message': process_message})
    #         if len(operation_id.operation_ids) <= 0:
    #             operation_id.sudo().unlink()
    #         bigcommerce_store_id.bigcommerce_operation_message = " Import Pricelist Process Complete "
