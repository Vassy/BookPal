# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

import base64
import contextlib
import csv
import io

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import pycompat

email_regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'


class SaleMultiShip(models.Model):
    _name = 'sale.multi.ship'
    _description = "Sale Order Multi Ship Line"

    sale_id = fields.Many2one(
        'sale.order', string="Sale Order", help='Linked Sale Order')

    csv_file = fields.Binary(
        string='CSV File', help="CSV File to update Shipping Line Data")

    csv_file_name = fields.Char(
        string="File Name", help="CSV File Name to update Shipping Line Data")

    multi_ship_export_template = fields.Binary(
        string="Export Template",
        help="CSV File to export Shipping and Product Variant Data")

    multi_ship_export_template_name = fields.Char(
        string="Export Template FIle Name",
        help="CSV File Name to export shipping and Product Variant Data")

    qty_csv_file = fields.Binary(
        string='Updated CSV File',
        help="Quantity Update CSV File to update Shipping Line Data")

    qty_csv_file_name = fields.Char(
        string="Updated CSV File Name",
        help="Quantity Update CSV File Name to update Shipping Line Data")

    partner_ids = fields.One2many(
        'res.partner', 'multi_ship_id',
        string='Customer Ship Lines',
        help="Split Shipping lines for different shipping addresses")

    def export_customer_shipping_detail_template(self):
        with contextlib.closing(io.BytesIO()) as csvfile:
            filename = "Export Customer Template - %s" % (self.sale_id.name)
            writer = pycompat.csv_writer(csvfile, dialect='UNIX')

            # Write Headers in CSV File
            csv_header = ['Addressee', 'Address',
                          'Address2', 'City', 'State', 'Zip',
                          'Country', 'Phone', 'Email',
                          'Attention', 'Method']
            value_count = 0
            for so_line in self.sale_id.order_line:
                if so_line.product_type == 'product':
                    if so_line.product_id.product_template_attribute_value_ids:
                        val_str = so_line.product_id.name + '(' + ','.join(
                            so_line.product_id.
                            product_template_attribute_value_ids.
                            mapped('name')) + ')'
                    else:
                        val_str = so_line.product_id.name
                    value_count += 1
                    csv_header.extend(
                        [val_str, 'Personalization 1', 'Personalization 2'])
            writer.writerow(csv_header)

            out = base64.encodebytes(csvfile.getvalue())
            self.write({
                'multi_ship_export_template': out,
                'multi_ship_export_template_name': filename + ".csv",
            })
        return {
            'type': 'ir.actions.act_url',
            'name': 'Shipment for Sale Lines',
            'url': '/web/content/sale.multi.ship/%s/'
                   'multi_ship_export_template/%s?download=true' % (
                    self and self.ids[0] or False,
                    self.multi_ship_export_template_name),
        }

    def import_customer_shipping_detail_template(self):
        context = self.env.context.copy()
        form_view_id = self.env.ref(
            'bista_sale_multi_ship.sale_order_multi_ship_form_wizard')
        line_vals = []

        if not self.qty_csv_file:
            raise UserError(_("You need to select a file!"))
        if self.qty_csv_file_name.split('.')[-1] not in ['csv', 'CSV']:
            raise UserError(_("Please upload Xls format file!"))
        if not self.qty_csv_file_name.split('.csv')[0].count('-') or \
            self.qty_csv_file_name.split('.csv')[0].count(
                '-') > 1:
            raise UserError(
                _("Please upload file with sale order : %s" %
                    self.sale_id.name))
        qty_csv_file_name = self.qty_csv_file_name.split('.csv')[
            0].split('-')[1]
        if qty_csv_file_name.strip() != self.sale_id.name:
            raise UserError(
                _("Please upload file with sale order : %s") %
                self.sale_id.name)

        binary_data = self.qty_csv_file
        x = base64.decodebytes(binary_data).decode('utf-8')
        str_file = io.StringIO(x, newline='\n')
        reader = csv.reader(str_file)

        so_lines = self.sale_id.order_line.filtered(
            lambda line: line.product_type == 'product')
        so_line_count = len(so_lines) if so_lines else 0

        order_lines = self.env['sale.order.line']
        count = 0

        for row in reader:
            if not row[1]:
                continue
            if count == 0:
                for col in range(11, 11 + (so_line_count * 3)):
                    product_name = str(row[col]).split('(')[0]
                    product_variant_str = str(
                        row[col]).split('(')[-1].split(')')[0]
                    matching_line = self.sale_id.order_line.filtered(
                        lambda line: line.product_id.name ==
                        product_name and ','.join(
                            line.product_id.
                            product_template_attribute_value_ids.
                            mapped('name')) == product_variant_str)
                    if not matching_line:
                        matching_line = self.sale_id.order_line.filtered(
                            lambda line: line.product_id.name == product_name)
                    order_lines |= matching_line
                    continue
            else:
                country_id = self.env['res.country'].search(
                    [('name', '=', str(row[6]))], limit=1)
                state_id = self.env['res.country.state'].search(
                    [('code', '=', str(row[4].strip())),
                     ('country_id', '=', country_id.id)], limit=1)
                carrier_id = self.env['delivery.carrier'].search(
                    [('name', 'ilike', str(row[10])),
                     ('delivery_type', '=',
                        self.sale_id.partner_carrier_id.delivery_type)],
                    limit=1)
                contact_details = self.env['res.partner'].search(
                    [('name', '=', str(row[0].strip())),
                     ('phone', '=', str(row[7].strip())),
                     ('email', '=', str(row[8].strip())),
                     ('is_multi_ship', '=', True),
                     ('multi_ship_id', '=', self.id)])

                if not contact_details:
                    vals = {
                        'name': str(row[0].strip()),
                        'street': str(row[1].strip()),
                        'street2': str(row[2].strip()),
                        'city': str(row[3].strip()),
                        'state_id': state_id.id,
                        'zip': str(row[5].strip()),
                        'country_id': country_id.id,
                        'phone': str(row[7].strip()),
                        'email': str(row[8].strip()),
                        'attention': str(row[9].strip()),
                        'property_delivery_carrier_id': carrier_id.id
                        if carrier_id else False,
                        'type': 'delivery',
                        'is_multi_ship': True,
                    }
                    col = 11
                    product_array = []
                    for order_line in order_lines:
                        total_qty = float(row[col] or 0.0)
                        if total_qty > 0:
                            product_array.append((0, 0, {
                                'so_line_id': order_line.id,
                                'personalization_1': row[col + 1].strip(),
                                'personalization_2': row[col + 2].strip(),
                                'product_qty': total_qty
                            }))
                        col += 3

                    if vals:
                        vals.update({'split_so_lines': product_array})
                        line_vals.append((0, 0, vals))
            count += 1

        if line_vals:
            self.partner_ids = line_vals
        return {
            'name': "Shipment for Sale Lines",
            'view_mode': 'form',
            'view_id': form_view_id.id,
            'res_model': 'sale.multi.ship',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'res_id': self and self.ids[0] or False,
            'context': context
        }

    def action_validate_customer_data(self):
        context = self.env.context.copy()
        form_view_id = self.env.ref(
            'bista_sale_multi_ship.sale_order_multi_ship_form_wizard')
        if self.partner_ids:
            self.partner_ids.verify_customer_details()
        return {
            'name': "Shipment for Sale Lines",
            'view_mode': 'form',
            'view_id': form_view_id.id,
            'res_model': 'sale.multi.ship',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'res_id': self and self.ids[0] or False,
            'context': context
        }


class SaleMultiShipQtyLines(models.Model):
    _name = 'sale.multi.ship.qty.lines'
    _description = 'Sale Order Line Split Qty'
    _rec_name = 'so_line_id'

    so_line_dom = fields.Char('Sale order line domain')
    so_line_id = fields.Many2one(
        'sale.order.line', 'Sale Order Line',
        help="Linked Sale Order Line")
    order_id = fields.Many2one("sale.order", "Order Reference")
    product_id = fields.Many2one(
        'product.product',
        related='so_line_id.product_id',
        store=True,
        string="Product",
        help='Name of Product from linked Sale Order Lines')
    product_uom_qty = fields.Float(
        related='so_line_id.product_uom_qty',
        string="Ordered Qty", help='Product Quantity')
    product_qty = fields.Float(string="Product Qty")
    personalization_1 = fields.Char('Personalization 1')
    personalization_2 = fields.Char('Personalization 2')

    partner_id = fields.Many2one(
        'res.partner', string="Shipment Details", ondelete='cascade')
    # Fields only for display purpose from SO Line
    name = fields.Char(related='partner_id.name')
    attention = fields.Char(related='partner_id.attention')
    property_delivery_carrier_id = fields.Many2one(
        related='partner_id.property_delivery_carrier_id')
    stock_picking_id = fields.Many2one(
        related='partner_id.stock_picking_id')
    carrier_track_ref = fields.Char(
        related='partner_id.carrier_track_ref')
    city = fields.Char(related='partner_id.city', help="City to Ship")
    state_id = fields.Many2one(
        "res.country.state",
        related='partner_id.state_id',
        help="State to Ship")
    country_id = fields.Many2one(
        'res.country', related='partner_id.country_id',
        help="Country to Ship")
    zip = fields.Char(related='partner_id.zip', help="Zip Code to Ship")
    shipping_date = fields.Date('Shipping Date')
    route_id = fields.Many2one('stock.location.route', 'Route')
    remain_qty = fields.Float(
        'Remaining Qty')

    def name_get(self):
        """Updated the display name."""
        res = []
        for rec in self:
            if rec.product_id:
                if rec.product_id.product_template_attribute_value_ids:
                    name = rec.product_id.name + "(" + ','.join(
                        rec.product_id.product_template_attribute_value_ids.
                        mapped('name')) + ")" + " - " + str(
                        rec.product_qty)
                else:
                    name = rec.product_id.name + " - " + str(rec.product_qty)
                res.append((rec.id, name))
        return res
