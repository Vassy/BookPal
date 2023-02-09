# Copyright 2015 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Sale Advance Payment",
    "version": "15.0.1.0.1",
    "author": "Comunitea, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-workflow",
    "category": "Sales",
    "license": "AGPL-3",
    "summary": "Allow to add advance payments on sales and then "
                "use them on invoices",
    "depends": ["bista_sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_view.xml",
        "wizard/sale_advance_payment_wzd_view.xml",
    ],
    "installable": True,
}
