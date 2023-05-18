# -*- coding: utf-8 -*-

from odoo import fields, models, tools


class SellerReport(models.Model):
    _name = "best.seller.report"
    _auto = False
    _description = "Best Seller Report"

    order_id = fields.Many2one("sale.order", string="Order Number")
    order_date = fields.Date(string="Order Date")
    product_id = fields.Many2one("product.product", string="Product Title")
    sku = fields.Char(string="SKU")
    customer_email = fields.Char(string="Order Customer Email Address")
    quantity = fields.Integer(string="Quantity")
    publication_date = fields.Date(string="Publication Date")
    shipping_zip_code = fields.Char(string="Shipping Address Zip Code")
    order_company = fields.Many2one("res.company", string="Order Company")
    order_status = fields.Selection(
        [
            ("draft", "Draft Quotation"),
            ("sent", "Quotation Sent"),
            ("done", "Sales Done"),
            ("cancel", "Cancelled"),
            ("quote_approval", "Quotation In Approval"),
            ("quote_confirm", "Approved Quotation"),
            ("order_booked", "Order Booked"),
            ("pending_for_approval", "Order In Approval"),
            ("sale", "Approved Order"),
        ],
        string="Order Status",
    )
    industry_id = fields.Many2one(
        "res.partner.industry", string="Order Customer Segment"
    )
    partner_id = fields.Many2one("res.partner", string="Order Account")
    fulfilment_project = fields.Boolean(string="Fulfilment Project")
    report_type = fields.Selection(
        [
            ("individual", "Individual"),
            ("bulk", "Bulk"),
            ("mixed", "Mixed"),
        ],
        string="Report Type",
    )
    report_date = fields.Date(string="Report Date")
    reported = fields.Boolean(string="Reported")
    product_tmpl_id = fields.Many2one(related="product_id.product_tmpl_id")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        date_type = self._context.get("date_type", False)
        start_date = self._context.get("start_date", False)
        end_date = self._context.get("end_date", False)
        report_type = self._context.get("report_type", False)
        industry_ids = self._context.get("industry_ids", False)
        select_str = """
            SELECT
                sale_order_line.id AS ID,
                sale_order.id AS order_id,
                sale_order.date_order AS order_date,
                sale_order_line.product_id AS product_id,
                product_product.default_code AS sku,
                product_template.publication_date AS publication_date,
                res_partner.email AS customer_email,
                res_partner.industry_id AS industry_id,
                res.zip AS shipping_zip_code,
                CAST(sale_order_line.product_uom_qty AS INT) AS quantity,
                sale_order.company_id AS order_company,
                sale_order_line.state AS order_status,
                sale_order.report_type AS report_type,
                sale_order.partner_id AS partner_id,
                sale_order.fulfilment_project AS fulfilment_project,
                sale_order.report_date AS report_date,
                sale_order.reported AS reported
        """
        from_str = """
            FROM sale_order_line
                JOIN sale_order ON (sale_order_line.order_id = sale_order.id)
                JOIN product_product ON (sale_order_line.product_id = product_product.id)
                JOIN product_template ON (product_product.product_tmpl_id = product_template.id)
                JOIN res_partner ON (sale_order.partner_id = res_partner.id)
                JOIN res_partner res ON (sale_order.partner_shipping_id = res.id)
        """
        where_str = (
            "WHERE sale_order.is_report = True"
            " AND sale_order.state in ('order_booked', 'sale', 'done')"
            " AND product_template.is_never_report = False"
        )
        if start_date and end_date:
            where_str += " AND sale_order.%s::date BETWEEN '%s' AND '%s'" % (
                date_type,
                start_date,
                end_date,
            )
        if report_type:
            where_str += " AND sale_order.report_type = '%s'" % (report_type)
        if industry_ids:
            where_str += (
                " AND (res_partner.industry_id NOT IN (%s) OR res_partner.industry_id IS NULL)"
                % ",".join(str(industry) for industry in industry_ids)
            )
        self.env.cr.execute(
            """CREATE or REPLACE VIEW %s as (%s %s %s)"""
            % (self._table, select_str, from_str, where_str)
        )
