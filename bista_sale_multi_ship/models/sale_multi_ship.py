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
from collections import defaultdict
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import pycompat
from odoo.exceptions import ValidationError

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
        """Export customer shipping detail."""
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
        """Import customer shipping details."""
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
        """Action validate customer data."""
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

    def _get_schedule_date(self):
        for line in self:
            date_deadline = line.shipping_date
            if not line.shipping_date:
                date_deadline = line.order_id.date_order + \
                    timedelta(days=line.so_line_id.customer_lead or 0.0)
        return date_deadline

    so_line_dom = fields.Char('Sale order line domain')
    so_line_id = fields.Many2one(
        'sale.order.line', 'Product',
        help="Linked Sale Order Line")
    order_id = fields.Many2one("sale.order", "Order Reference")
    product_id = fields.Many2one(
        'product.product',
        related='so_line_id.product_id',
        store=True,
        string="Shipment Product",
        help='Name of Product from linked Sale Order Lines')
    product_uom_qty = fields.Float(
        related='so_line_id.product_uom_qty',
        string="Ordered Qty", help='Product Quantity')
    product_uom = fields.Many2one(
        related="so_line_id.product_uom", store=True)
    product_qty = fields.Float(string="Shipping Qty")
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
    shipping_date = fields.Date('Need By Date')
    route_id = fields.Many2one('stock.location.route', 'Routes')
    remain_qty = fields.Float(
        'Unplanned Qty')
    move_ids = fields.One2many(
        'stock.move', 'multi_ship_line_id', 'Stock Moves')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('deliver', 'Delivered'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('short_close', 'Short Closed')],
        string='Shipping Status',
        readonly=True, copy=False, index=True, tracking=3,
        default='draft')
    partner_state = fields.Selection(
        related="partner_id.state", string='Contact status')
    display_qty_widget = fields.Boolean(
        related="so_line_id.display_qty_widget")
    qty_delivered = fields.Float(
        'Delivered Quantity', copy=False,
        compute='_compute_qty_delivered',
        inverse='_inverse_qty_delivered',
        store=True, digits='Product Unit of Measure',
        default=0.0)
    qty_short_close = fields.Float(
        'Short Closed Qty',
        compute="_compute_qty_short_close",
        store=True)
    qty_delivered_manual = fields.Float(
        'Delivered Manually', copy=False,
        digits='Product Unit of Measure', default=0.0)
    qty_invoiced = fields.Float(related="so_line_id.qty_invoiced")
    qty_delivered_method = fields.Selection(
        related="so_line_id.qty_delivered_method", store=True)
    product_type = fields.Selection(related='product_id.detailed_type')
    virtual_available_at_date = fields.Float(
        compute='_compute_qty_at_date', digits='Product Unit of Measure')
    scheduled_date = fields.Date(compute='_compute_qty_at_date')
    forecast_expected_date = fields.Datetime(compute='_compute_qty_at_date')
    free_qty_today = fields.Float(
        compute='_compute_qty_at_date', digits='Product Unit of Measure')
    qty_available_today = fields.Float(compute='_compute_qty_at_date')
    warehouse_id = fields.Many2one(related='order_id.warehouse_id')
    qty_to_deliver = fields.Float(
        compute='_compute_qty_to_deliver', digits='Product Unit of Measure')
    is_mto = fields.Boolean(compute='_compute_is_mto')
    display_qty_widget = fields.Boolean(compute='_compute_qty_to_deliver')
    purchase_line_ids = fields.One2many(
        'purchase.order.line',
        'multi_ship_line_id',
        string="Generated Purchase Lines",
        readonly=True,
        help="Purchase line generated by this Sales item"
             " on order confirmation, "
             "or when the quantity was increased.")
    supplier_id = fields.Many2one('res.partner', 'Vendor')
    is_expense = fields.Boolean()

    @api.depends('product_id', 'route_id',
                 'order_id.warehouse_id',
                 'product_id.route_ids', 'so_line_id.route_id')
    def _compute_is_mto(self):
        self.is_mto = False
        for line in self:
            if not line.display_qty_widget or line.is_mto:
                continue

            product = line.product_id
            product_routes = line.route_id or \
                line.so_line_id.route_id or (
                    product.route_ids + product.categ_id.total_route_ids)

            # Check MTO
            mto_route = line.order_id.warehouse_id.mto_pull_id.route_id
            if not mto_route:
                try:
                    mto_route = self.env['stock.warehouse']._find_global_route(
                        'stock.route_warehouse0_mto', _('Make To Order'))
                except UserError:
                    # if route MTO not found in ir_model_data, we treat the
                    # product as in MTS
                    pass

            if mto_route and mto_route in product_routes:
                line.is_mto = True
            else:
                line.is_mto = False
            # check dropshipping
            for pull_rule in product_routes.mapped('rule_ids'):
                if pull_rule.picking_type_id.sudo().\
                        default_location_src_id.usage == 'supplier' and\
                        pull_rule.picking_type_id.sudo().\
                        default_location_dest_id.usage == 'customer':
                    line.is_mto = True
                    break

    @api.onchange('so_line_id')
    def onchange_so_line_id(self):
        """Set default schedule date."""
        if self.so_line_id:
            self.shipping_date = self._get_schedule_date()

    @api.depends('product_type', 'product_uom_qty',
                 'qty_delivered', 'state', 'move_ids', 'product_uom')
    def _compute_qty_to_deliver(self):
        """Compute the visibility of the inventory widget."""
        for line in self:
            line.qty_to_deliver = line.product_qty - line.qty_delivered
            if line.state in ('draft', 'sent', 'sale') and \
                    line.product_type == 'product' and \
                    line.qty_to_deliver > 0:
                if line.state == 'sale' and not line.move_ids:
                    line.display_qty_widget = False
                else:
                    line.display_qty_widget = True
            else:
                line.display_qty_widget = False

    @api.depends(
        'product_id', 'product_qty', 'order_id.commitment_date',
        'move_ids', 'move_ids.forecast_expected_date',
        'move_ids.forecast_availability')
    def _compute_qty_at_date(self):
        """Compute the quantity forecasted of product at delivery date.

        There are two cases:
         1. The quotation has a commitment_date, we take it as
            delivery date
         2. The quotation hasn't commitment_date, we compute the
            estimated delivery
            date based on lead time
        """
        treated = self.browse()
        # If the state is already in sale the picking is created and a
        # simple forecasted quantity isn't enough
        # Then used the forecasted data of the related stock.move
        for quat_line in self.filtered(lambda li: li.state == 'draft'):
            quat_line.scheduled_date = quat_line._get_schedule_date()
        for line in self.filtered(lambda l: l.state == 'sale'):
            if not line.display_qty_widget:
                continue
            moves = line.move_ids.filtered(
                lambda m: m.product_id == line.product_id)
            line.forecast_expected_date = max(moves.filtered(
                "forecast_expected_date").mapped(
                "forecast_expected_date"), default=False)
            line.qty_available_today = 0
            line.free_qty_today = 0
            for move in moves:
                line.qty_available_today += move.product_uom._compute_quantity(
                    move.reserved_availability, line.product_uom)
                line.free_qty_today += move.product_id.uom_id.\
                    _compute_quantity(
                        move.forecast_availability, line.product_uom)
            line.scheduled_date = line._get_schedule_date()
            line.virtual_available_at_date = False
            treated |= line

        qty_processed_per_product = defaultdict(lambda: 0)
        grouped_lines = defaultdict(
            lambda: self.env['sale.multi.ship.qty.lines'])
        # We first loop over the SO lines to group them by
        # warehouse and schedule
        # date in order to batch the read of the quantities computed field.
        for line in self.filtered(lambda l: l.state in ('draft', 'sent')):
            if not (line.product_id and line.display_qty_widget):
                continue
            grouped_lines[(
                line.warehouse_id.id, line.scheduled_date)] |= line

        for (warehouse, scheduled_date), lines in grouped_lines.items():
            product_qties = lines.mapped('product_id').with_context(
                to_date=scheduled_date, warehouse=warehouse).read([
                    'qty_available',
                    'free_qty',
                    'virtual_available',
                ])
            qties_per_product = {
                product['id']: (product['qty_available'],
                                product['free_qty'],
                                product['virtual_available'])
                for product in product_qties
            }
            for line in lines:
                qty_available_today, free_qty_today, \
                    virtual_available_at_date = qties_per_product[
                        line.product_id.id]
                line.qty_available_today = qty_available_today - \
                    qty_processed_per_product[line.product_id.id]
                line.free_qty_today = free_qty_today - \
                    qty_processed_per_product[line.product_id.id]
                line.virtual_available_at_date = virtual_available_at_date - \
                    qty_processed_per_product[line.product_id.id]
                line.forecast_expected_date = False
                product_qty = line.product_uom_qty
                if line.product_uom and line.product_id.uom_id and \
                        line.product_uom != line.product_id.uom_id:
                    line.qty_available_today = line.product_id.uom_id.\
                        _compute_quantity(
                            line.qty_available_today, line.product_uom)
                    line.free_qty_today = line.product_id.uom_id.\
                        _compute_quantity(
                            line.free_qty_today, line.product_uom)
                    line.virtual_available_at_date = line.product_id.uom_id.\
                        _compute_quantity(
                            line.virtual_available_at_date, line.product_uom)
                    product_qty = line.product_uom._compute_quantity(
                        product_qty, line.product_id.uom_id)
                qty_processed_per_product[line.product_id.id] += product_qty
            treated |= lines
        remaining = (self - treated)
        remaining.virtual_available_at_date = False
        remaining.forecast_expected_date = False
        remaining.scheduled_date = False
        remaining.free_qty_today = False
        remaining.qty_available_today = False

    def _get_outgoing_incoming_moves(self):
        outgoing_moves = self.env['stock.move']
        incoming_moves = self.env['stock.move']

        moves = self.move_ids.filtered(
            lambda r: r.state != 'cancel' and not
            r.scrapped and self.product_id == r.product_id and
            r.picking_type_id.code in ['outgoing', 'incoming'])
        if self._context.get('accrual_entry_date'):
            moves = moves.filtered(
                lambda r: fields.Date.to_date(
                    r.date) <= self._context['accrual_entry_date'])
        for move in moves:
            if move.location_dest_id.usage == "customer":
                if not move.origin_returned_move_id or (
                        move.origin_returned_move_id and move.to_refund):
                    outgoing_moves |= move
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                incoming_moves |= move
            elif move.location_dest_id.usage == "supplier" and move.to_refund:
                outgoing_moves |= move
            elif move.location_dest_id.usage != "supplier":
                if not move.origin_returned_move_id or (
                        move.origin_returned_move_id and move.to_refund):
                    incoming_moves |= move
        return outgoing_moves, incoming_moves

    @api.depends('move_ids.state',
                 'move_ids.scrapped', 'move_ids.product_uom_qty',
                 'move_ids.product_uom',
                 'qty_delivered_method',
                 'qty_delivered_manual')
    def _compute_qty_delivered(self):
        # Just ignore for timesheet may need to check in future.
        # lines_by_analytic = self.filtered(
        #     lambda sol: sol.qty_delivered_method == 'analytic')
        # mapping = lines_by_analytic._get_delivered_quantity_by_analytic(
        #     [('amount', '<=', 0.0)])
        # for so_line in lines_by_analytic:
        #     so_line.qty_delivered = mapping.get(
        #         so_line.id or so_line._origin.id, 0.0)
        for line in self:  # TODO: maybe one day, this should be done in SQL
            # for performance sake
            if line.qty_delivered_method == 'stock_move':
                qty = 0.0
                outgoing_moves, incoming_moves = line.\
                    _get_outgoing_incoming_moves()
                for move in outgoing_moves:
                    if move.state != 'done':
                        continue
                    qty += move.product_uom._compute_quantity(
                        move.product_uom_qty,
                        line.product_uom, rounding_method='HALF-UP')
                for move in incoming_moves:
                    if move.state != 'done':
                        continue
                    qty -= move.product_uom._compute_quantity(
                        move.product_uom_qty, line.product_uom,
                        rounding_method='HALF-UP')
                line.qty_delivered = qty
            elif line.qty_delivered_method == 'manual':
                line.qty_delivered = line.qty_delivered_manual or 0.0
            if line.product_qty and line.qty_delivered == line.product_qty:
                line.state = 'deliver'

    @api.depends('state')
    def _compute_qty_short_close(self):
        for rec in self:
            rec.qty_short_close = 0
            if rec.state == 'short_close':
                rec.qty_short_close = rec.product_qty - rec.qty_delivered

    @api.onchange('qty_delivered')
    def _inverse_qty_delivered(self):
        """Inverse qty delivered.

        When writing on qty_deliveredif the value should be modify manually
        (`qty_delivered_method` = 'manual' only),
        then we put the value in `qty_delivered_manual`.
        Otherwise, `qty_delivered_manual` should be False since the
        delivered qty is automatically compute by other mecanisms.
        """
        for line in self:
            if line.qty_delivered_method == 'manual':
                line.qty_delivered_manual = line.qty_delivered
            else:
                line.qty_delivered_manual = 0.0

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

    def _get_qty_procurement(self, previous_product_uom_qty=False):
        self.ensure_one()
        # People without purchase rights should be able to do this operation
        purchase_lines_sudo = self.sudo().purchase_line_ids
        if purchase_lines_sudo.filtered(lambda r: r.state != 'cancel'):
            qty = 0.0
            for po_line in purchase_lines_sudo.filtered(
                    lambda r: r.state != 'cancel'):
                qty += po_line.product_uom._compute_quantity(
                    po_line.product_qty,
                    self.product_uom,
                    rounding_method='HALF-UP')
            return qty
        else:
            qty = 0.0
            outgoing_moves, incoming_moves = self.\
                _get_outgoing_incoming_moves()
            for move in outgoing_moves:
                qty += move.product_uom._compute_quantity(
                    move.product_uom_qty, self.product_uom,
                    rounding_method='HALF-UP')
            for move in incoming_moves:
                qty -= move.product_uom._compute_quantity(
                    move.product_uom_qty, self.product_uom,
                    rounding_method='HALF-UP')
            return qty

    # def write(self, values):
    #     """Overide method to create delivery when update shipping qty."""
    #     lines = self.env['sale.multi.ship.qty.lines']
    #     if 'product_qty' in values:
    #         lines = self.filtered(
    #             lambda r: r.state == 'sale' and not r.is_expense)

    #     previous_product_uom_qty = {
    #         line.id: line.product_qty for line in lines}
    #     res = super(SaleMultiShipQtyLines, self).write(values)
    #     if lines:
    #         order_lines = lines.mapped('so_line_id')
    #         order_lines._action_launch_stock_rule(previous_product_uom_qty)
    #     if 'shipping_date' in values and self.state == 'sale' and not \
    #             self.order_id.commitment_date:
    #         # Propagate deadline on related stock move
    #         self.move_ids.date_deadline = self.shipping_date
    #     return res

    # @api.model_create_multi
    # def create(self, vals_list):
    #     """When add shipping line in confirm sale order."""
    #     lines = super(SaleMultiShipQtyLines, self).create(vals_list)
    #     order_lines = lines.mapped('so_line_id').filtered(
    #         lambda line: line.state == 'sale')
    #     if order_lines:
    #         lines.mapped('partner_id').verify_customer_details()
    #         if lines.filtered(lambda x: x.state != 'verified'):
    #             raise ValidationError('Please verfiy the shipment details')
    #         order_lines._action_launch_stock_rule()
    #     return lines

    def cancel_shipment(self):
        """Cancel the ready or waiting move operation line."""
        flag = True
        for rec in self:
            todo_move = rec.move_ids.filtered(lambda x: x.state != 'done')
            for move in todo_move.mapped('move_orig_ids'):
                if move.picking_type_id.code == 'incoming' and \
                    move.purchase_line_id and \
                        move.purchase_line_id.state == 'purchase':
                    flag = False
                    todo_move -= move.move_dest_ids
            done_move = rec.move_ids.filtered(lambda x: x.state == 'done')
            if todo_move and not done_move and flag:
                rec.state = 'draft'
                old_qty = rec.product_qty
                rec.product_qty = 0
                rec.so_line_id._action_launch_stock_rule(old_qty)
            todo_move._action_cancel()
            cancel_state = 'cancel'
            if todo_move and rec.qty_delivered > 0:
                cancel_state = 'short_close'

            rec.state = cancel_state
            rec.order_id.onchange_sale_multi_ship_qty_lines()

    def unlink(self):
        """Restrict to unlnk shipment if its not cancel or draft."""
        for rec in self:
            if rec.state not in ['cancel', 'draft']:
                raise ValidationError("You can delete only cancel shipment.")
            if rec.move_ids.filtered(
                    lambda x: x.state == 'done'):
                raise ValidationError("This shipment has some done move")
        return super(SaleMultiShipQtyLines, self).unlink()
