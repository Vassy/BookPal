# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class SellerReport(models.Model):
    _name = 'best.seller.report'
    _auto = False
    _description = 'Best Seller Report'

    order_number = fields.Char(string='Order Number')
    order_date = fields.Date(string='Order Date')
    product_id = fields.Many2one('product.product',string='Product Title')
    sku = fields.Char(string='SKU')
    customer_email = fields.Char(string='Order Customer Email Address')
    quantity = fields.Float(string='Quantity')
    publication_date = fields.Date(string='Publication Date')
    shipping_zip_code = fields.Char(string='Shipping Address Zip Code')
    # order_account = fields.Char(string='Order Account')
    order_company = fields.Many2one('res.company', string='Order Company')
    # customer_segment = fields.Char(string='Order Customer Segment')
    order_status = fields.Selection([
        ("draft", "Draft Quotation"),
        ("sent", "Quotation Sent"),
        ("done", "Sales Done"),
        ("cancel", "Cancelled"),
        ("quote_approval", "Quotation In Approval"),
        ("quote_confirm", "Approved Quotation"),
        ("order_booked", "Order Booked"),
        ("pending_for_approval", "Order In Approval"),
        ("sale", "Approved Order")
        ], string='Order Status')
    industry_id = fields.Many2one('res.partner.industry', string='Industry')

    def init(self):
        """ Fetch the data from sale order line based on report type and start and end date """
        tools.drop_view_if_exists(self.env.cr, self._table)
        start_date = self._context.get('ctx', False).get('start_date', False) \
                    if self._context.get('ctx', False) else False
        end_date = self._context.get('ctx', False).get('end_date', False) \
                    if self._context.get('ctx', False) else False
        report_type = self._context.get('ctx', False).get('report_type', False) \
                    if self._context.get('ctx', False) else False
        select_str = """ SELECT 
                            sale_order_line.id AS ID,
                            sale_order.name AS order_number,
                            sale_order.date_order AS order_date,
                            sale_order_line.product_id AS product_id,
                            product_product.default_code AS sku,
                            product_template.publication_date AS publication_date,
                            res_partner.email AS customer_email,
                            res_partner.industry_id AS industry_id,
                            res.zip AS shipping_zip_code,
                            sale_order_line.product_uom_qty AS quantity,
                            sale_order.company_id AS order_company,
                            sale_order_line.state AS order_status
                        """
        from_str = """ FROM sale_order_line
                        JOIN sale_order ON (sale_order_line.order_id = sale_order.id)
                        JOIN product_product ON (sale_order_line.product_id = product_product.id)
                        JOIN product_template ON (product_product.product_tmpl_id = product_template.id)
                        JOIN res_partner ON (sale_order.partner_id = res_partner.id)
                        JOIN res_partner res ON (sale_order.partner_shipping_id = res.id)
                    """
        where_str = """ WHERE
                            sale_order.is_report = True AND product_template.is_never_report = False
                        """
        if start_date and end_date:
            where_str = where_str + "AND sale_order.date_order::date BETWEEN '%s' AND '%s'" % (start_date, end_date)
        if report_type:
            where_str = where_str + "AND sale_order.report_type = '%s'" % (report_type)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s %s %s)""" % (self._table, \
             select_str, from_str, where_str))
