# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from datetime import timedelta

from odoo.tools import float_compare
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.sale_stock.models.sale_order import SaleOrderLine as \
    BaseSaleOrderLine


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    so_lines = fields.Char(default="[]", copy=False)
    sale_ship_lines = fields.One2many(
        'sale.multi.ship', 'sale_id', string="Sale Multi Shipment")

    sale_multi_ship_qty_lines = fields.One2many(
        'sale.multi.ship.qty.lines', 'order_id',
        string="Multi Ship Lines",
        help='Linked With Sale Multi Ship Lines')

    customer_drop_ship_file = fields.Binary(
        'Customer Drop Ship File', attachment=True)

    # partner_ids = fields.One2many(
    #     'res.partner', 'sale_id',
    #     domain=[('split_so_lines', '!=', False)],
    #     string="Multi Ship Lines")

    split_shipment = fields.Boolean(
        'Multi Shipments?', default=False, copy=False,
        help="Check this box if you have multiple shipment \
        locations for products on the same order.\
        Clicking this checkbox will make the Multi-Ship \
        tab appear on the Sales Order. Visit TeamWorld \
        University and search for Quotes and Sales Order\
        with Multiple Shipments for detailed instructions.")
    # is_individual = fields.Boolean('Create Individual Shipment Contact?')

    ship_lines_validated = fields.Boolean(string='Ship Lines Validated')
    # Third Party Billing
    third_party_shipper = fields.Char(string='Third Party Shipper #')
    partner_carrier_id = fields.Many2one(
        'delivery.carrier', string='Delivery Carrier')

    ups_bill_my_account = fields.Boolean(
        related='partner_carrier_id.ups_bill_my_account', readonly=True)
    is_confirm_ship = fields.Boolean(
        'Confirm Shipment', compute="_compute_confirm_shipment")

    def _compute_confirm_shipment(self):
        for rec in self:
            if rec.state == 'sale' and \
                rec.sale_multi_ship_qty_lines.filtered(
                    lambda x: x.state in ['draft', 'order_booked']):
                rec.is_confirm_ship = True
            else:
                rec.is_confirm_ship = False

    def action_approval(self):
        if self.split_shipment and self.sale_multi_ship_qty_lines.filtered(
            lambda sp: not sp.route_id and sp.product_id.type != "service" and sp.state not in ['sale', 'done', 'cancel'] 
        ):
            raise ValidationError("Please set routes on shipment lines.")
        if not self.split_shipment and self.order_line.filtered(
            lambda l: not l.route_id and l.product_id.type != "service" and l.state not in ['sale', 'done', 'cancel']
        ):
            raise ValidationError("Please set routes on order lines.")
        if not self.split_shipment and self.order_line.filtered(
            lambda l: not l.supplier_id and l.product_id.type != "service" and l.state not in ['sale', 'done', 'cancel']
        ):
            raise ValidationError("Please set vendor on order lines.")
        return super().action_approval()

    def open_sale_multi_ship_wizard(self):
        """Open sale multi ship wizard."""
        context = self.env.context.copy()
        form_view_id = self.env.ref(
            'bista_sale_multi_ship.'
            'sale_order_multi_ship_form_wizard')
        context.update({'default_sale_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'view_id': form_view_id.id,
            'res_model': 'sale.multi.ship',
            'name': 'Shipment for Sale Lines',
            'res_id': self.sale_ship_lines and
                      self.sale_ship_lines.ids[0] or False,
            'context': context
        }

    def _split_shipping_process(self):
        # Method deprecated
        price_total = 0.0
        vals = {}
        delivery_carrier = self.env['delivery.carrier']
        prod_obj = self.env['product.product']

        if self.split_shipment and not self.sale_ship_lines:
            raise UserError(
                _('You can not split shipment without required data!'))
        multi_ship_wiz = self.partner_ids.mapped('multi_ship_id')
        delivery_type = self.partner_id.property_delivery_carrier_id

        if delivery_type == 'fedex':
            if not multi_ship_wiz.teamworld_shipping:
                price_total = 0.0
            else:
                price_total = delivery_carrier.fedex_rate_shipment(self)
            product_id = prod_obj.search(
                [('id', '=', self.env.ref(
                    'bista_sale_multi_ship.\
                    product_product_delivery_fedex_multiship').id)])
        if delivery_type == 'ups':
            if not multi_ship_wiz.teamworld_shipping:
                price_total = 0.0
            else:
                price_total = delivery_carrier.ups_rate_shipment(self)
            product_id = prod_obj.search(
                [('id', '=', self.env.ref('bista_sale_multi_ship.\
                        product_product_delivery_ups_multiship').id)])

        if delivery_type:
            vals.update({
                'order_id': self.id,
                'name': product_id.description_sale,
                'product_uom_qty': 1,
                'product_uom': product_id.uom_id.id,
                'product_id': product_id.id,
                'tax_id': [(6, 0, product_id.taxes_id.ids)],
                'is_delivery': True,
                'price_unit': price_total,
                'sequence': self.order_line[-1].sequence + 1
            })
            self.env['sale.order.line'].sudo().create(vals)

    def action_confirm(self):
        """Action confirm."""
        msg = ""
        if self.split_shipment and not self.sale_multi_ship_qty_lines:
            msg = _("Please add shipment plan to confirm the sale order.\n")
        else:
            verified_shipment_lines = self.sale_multi_ship_qty_lines.filtered(
                lambda msl: msl.partner_id.state != 'verified')
            if self.split_shipment and verified_shipment_lines:
                msg = _(
                    "Please verify the shipment details before "
                    "approving the sale order.\n")
            if self.split_shipment and \
                self.sale_multi_ship_qty_lines.filtered(
                    lambda x: x.product_qty == 0 and x.state not in ['sale', 'done', 'cancel']):
                msg = _("Please enter shipping qty.")

        # COMMENTED AS ALL THE LINES SHOULD BE VERIFIED WAS STOPPING
        # THE FLOW
        # if self.split_shipment and not self.ship_lines_validated:
        #     msg = _("Each multi ship lines must be verified to "
        #             "confirm the sale order.\n")
        #     error_shipment_lines = self.partner_ids.filtered(
        #         lambda msl: msl.state == 'error')
        #     if error_shipment_lines:
        #         name_string = ', '.join(
        #             map(str, error_shipment_lines.mapped('name')))
        #         if name_string:
        #             msg += _("Line with customers '%s' has error.\n" %
        #                      name_string)

        order_lines = self.order_line.filtered(
            lambda a: a.product_id.detailed_type == 'product')
        for order_line in order_lines:
            product_uom_qty = sum(order_line.mapped('product_uom_qty'))
            product_qty = sum(
                order_line.sale_multi_ship_qty_lines.filtered(
                    lambda l: l.state in [
                        'draft', 'sent',
                        'order_booked']).mapped('product_qty'))
            if self.split_shipment and product_uom_qty < product_qty:
                product_name = order_line.product_id.name
                if order_line.product_id.product_template_attribute_value_ids:
                    product_name = product_name + '(' + ','.join(
                        order_line.product_id.
                        product_template_attribute_value_ids.
                        mapped('name')) + ')'
                msg += _("For %s shipping qty %s is more than ordered "
                         "qty %s.\n" % (
                             product_name,
                             product_qty, product_uom_qty))

        if msg:
            raise ValidationError(msg)
        return super(SaleOrder, self).action_confirm()

    def action_send_for_approval(self):
        """Based on customer set delivery in shipping line."""
        msg = ""
        order_lines = self.order_line.filtered(
            lambda a: a.product_id.detailed_type == 'product')
        for order_line in order_lines:
            product_uom_qty = sum(order_line.mapped('product_uom_qty'))
            product_qty = sum(
                order_line.sale_multi_ship_qty_lines.filtered(
                    lambda l: l.state in [
                        'draft', 'sent', 'order_booked']).mapped(
                    'product_qty'))
            if self.split_shipment and product_uom_qty < product_qty:
                product_name = order_line.product_id.name
                if order_line.product_id.product_template_attribute_value_ids:
                    product_name = product_name + '(' + ','.join(
                        order_line.product_id.
                        product_template_attribute_value_ids.
                        mapped('name')) + ')'
                msg += _("For %s shipping qty %s is more than ordered "
                         "qty %s.\n" % (
                             product_name,
                             product_qty, product_uom_qty))
        if msg:
            raise ValidationError(msg)
        return super(SaleOrder, self).action_send_for_approval()

    def action_verify_customer_data(self):
        """Verify customer data."""
        for customer_line in self.sale_multi_ship_qty_lines.filtered(
                lambda cl: cl.partner_id.state != 'verified'):
            customer_line.partner_id.with_context(
                {'order_id': self.id}).verify_customer_details()

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """Based on customer set delivery in shipping line."""
        super(SaleOrder, self).onchange_partner_id()
        for rec in self:
            partner = rec.partner_id.parent_id or rec.partner_id
            rec.carrier_id = partner.property_delivery_carrier_id or False
            rec.partner_carrier_id = partner.property_delivery_carrier_id or \
                False
            if partner.property_delivery_carrier_id.ups_bill_my_account:
                rec.third_party_shipper = partner.property_ups_carrier_account
            else:
                rec.third_party_shipper = False

    def action_open_shiping_wizard(self):
        """Open shipping wizard."""
        wizard_external_shiping_view_id = self.env.ref(
            'bista_sale_multi_ship.view_external_shiping_wizard')
        return{
            'name': _('External Shipping'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'external.shipping',
            'view_id': wizard_external_shiping_view_id.id,
            'target': 'new'
        }

    @api.onchange('sale_multi_ship_qty_lines')
    def onchange_sale_multi_ship_qty_lines(self):
        """Based on sale multi ship lines calculate the remain qty."""
        old_ship_lines = self._origin.sale_multi_ship_qty_lines
        new_ship_lines = self.sale_multi_ship_qty_lines.ids
        for line in self.sale_multi_ship_qty_lines:
            total_prod_qty = sum(
                self.sale_multi_ship_qty_lines.filtered(
                    lambda x: x.so_line_id.id == line.so_line_id.id and
                    x.state != 'cancel').mapped(
                    'product_qty'))
            line.remain_qty = line.product_uom_qty - total_prod_qty
            for so_line in self.order_line:
                if so_line._origin.id and \
                        so_line._origin.id == line.so_line_id.id:
                    so_line.remain_so_qty = line.remain_qty
        for ship_line in old_ship_lines:
            if ship_line.id not in new_ship_lines:
                other_ship_line = self.sale_multi_ship_qty_lines.filtered(
                    lambda sl: sl.so_line_id.id ==
                    ship_line.so_line_id._origin.id and sl.state != 'cancel')
                if not other_ship_line:
                    so_old_line = self.order_line.filtered(
                        lambda l: l._origin.id == ship_line.so_line_id.id)
                    so_old_line.remain_so_qty = so_old_line.product_uom_qty
        filter_so_line = self.order_line.filtered(
            lambda x: x.remain_so_qty > 0)
        if self._origin.sale_multi_ship_qty_lines or \
                self.sale_multi_ship_qty_lines:
            so_lines = str(filter_so_line._origin.ids)
            self.so_lines = so_lines

    @api.onchange('order_line')
    def onchnage_order_lines(self):
        """Updated unplanned qty."""
        if self.env.context.get('multi_ship'):
            return
        for rec in self:
            for line in rec.order_line:
                planned_qty = sum(
                    line._origin.sale_multi_ship_qty_lines.filtered(
                        lambda sl: sl.so_line_id.id == line._origin.id and
                        sl.state != 'cancel').mapped(
                        'product_qty'))
                line.remain_so_qty = line.product_uom_qty - planned_qty
                lines = []
                if line.remain_so_qty and line._origin:
                    lines = str(eval(line.order_id.so_lines) + [
                        line._origin.id])
                rec.so_lines = lines

    @api.constrains('order_line')
    def set_so_lines(self):
        """Set order line in so lines for domain."""
        for rec in self:
            if not rec.sale_multi_ship_qty_lines:
                rec.so_lines = rec.order_line.ids

    def _action_cancel(self):
        res = super(SaleOrder, self)._action_cancel()
        for so in self:
            so.sale_multi_ship_qty_lines.filtered(
                lambda x: x.state != 'sale').write({'state': 'cancel'})
        return res

    def action_draft(self):
        """Set to draft shipping line."""
        res = super(SaleOrder, self).action_draft()
        for so in self:
            so.sale_multi_ship_qty_lines.write({'state': 'draft'})
        return res

    def confirm_shipment(self):
        """Confirm shipment after confirmed sale order."""
        msg = ""
        for so in self:
            if so.sale_multi_ship_qty_lines.filtered(
                    lambda x: x.state in ['draft', 'order_booked'] and
                    x.partner_id.state != 'verified'):
                raise ValidationError("Please verify the shipment details.")
            if so.sale_multi_ship_qty_lines.filtered(
                    lambda x: x.state in ['draft', 'order_booked'] and
                    not x.product_qty):
                raise ValidationError("Please enter the shipment qty.")
            if self.split_shipment and self.sale_multi_ship_qty_lines.filtered(
                lambda sp: not sp.route_id and
                sp.product_id.type != "service" and
                sp.state not in ['sale', 'done', 'cancel']
            ):
                raise ValidationError("Please set routes on shipment lines.")
            if not self.split_shipment and self.order_line.filtered(
                lambda l: not l.route_id and
                l.product_id.type != "service" and
                l.state not in ['sale', 'done', 'cancel']
            ):
                raise ValidationError("Please set routes on order lines.")
            order_lines = so.sale_multi_ship_qty_lines.filtered(
                lambda li: li.state in ['draft', 'order_booked']).mapped(
                    'so_line_id').filtered(
                lambda line: line.state == 'sale')
            for order_line in order_lines:
                product_uom_qty = sum(order_line.mapped('product_uom_qty'))
                product_qty = sum(
                    order_line.sale_multi_ship_qty_lines.filtered(
                        lambda l: l.state in
                        ['draft', 'sent', 'order_booked']).mapped(
                        'product_qty'))
                if self.split_shipment and product_uom_qty < product_qty:
                    product_name = order_line.product_id.name
                    if order_line.product_id.\
                            product_template_attribute_value_ids:
                        product_name = product_name + '(' + ','.join(
                            order_line.product_id.
                            product_template_attribute_value_ids.
                            mapped('name')) + ')'
                    msg += _("For %s shipping qty %s is more than ordered "
                             "qty %s.\n" % (
                                 product_name ,
                                 product_qty, product_uom_qty))
            if msg:
                raise ValidationError(msg)
            order_lines._action_launch_stock_rule()

    def print_shipment(self):
        """Print the shipment report."""
        report_action = self.env.ref(
            'bista_sale_multi_ship.shipment_report_action').read()[0]
        return report_action


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sale_multi_ship_qty_lines = fields.One2many(
        'sale.multi.ship.qty.lines', 'so_line_id',
        string="Multi Ship Lines",
        help='Linked With Sale Multi Ship Lines')
    remain_so_qty = fields.Float(
        "Unplanned Order Qty")
    supplier_id = fields.Many2one('res.partner', 'Vendor')
    vendor_shipping_cost = fields.Float("Vendor Shipping Cost")

    def open_sale_multi_ship_qty_wizard(self):
        """Open sale multi ship qty wizard."""
        context = self.env.context.copy()
        form_view_id = self.env.ref(
            'bista_sale_multi_ship.'
            'sale_order_multi_ship_qty_form_wizard')
        context.update({'default_so_line_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'view_id': form_view_id.id,
            'res_model': 'sale.order.line',
            'name': 'Shipment for Sale Lines',
            'res_id': self.id or False,
            'context': context
        }

    def _prepare_procurement_values(self, group_id=False):
        """Override method to update route , partner and shipping date."""
        if not self.order_id.split_shipment:
            return super(
                SaleOrderLine, self)._prepare_procurement_values(group_id)
        self.ensure_one()

        values = []
        date_deadline = self.order_id.commitment_date or (
            self.order_id.date_order + timedelta(
                days=self.customer_lead or 0.0))
        date_planned = date_deadline - timedelta(
            days=self.order_id.company_id.security_lead)
        for ship_line in self.sale_multi_ship_qty_lines.filtered(
            lambda l: l.partner_id.state == 'verified' and
                l.state in ['draft', 'order_booked']):
            proc_vals = {
                'group_id': group_id,
                'sale_line_id': self.id,
                'date_planned': date_planned,
                'date_deadline': date_deadline,
                'route_ids': self.route_id,
                'warehouse_id': self.order_id.warehouse_id or False,
                'partner_id': self.order_id.partner_shipping_id.id,
                'product_description_variants': self.with_context(
                    lang=self.order_id.partner_id.lang).
                _get_sale_order_line_multiline_description_variants(),
                'company_id': self.order_id.company_id,
                'product_packaging_id': self.product_packaging_id,
                'sequence': self.sequence,
                'product_uom_qty': ship_line.product_qty,
                'multi_ship_line_id': ship_line.id,
                'ship_line': ship_line
            }
            if ship_line.partner_id:
                proc_vals.update({
                    'partner_id': self.order_partner_id.id})
            if ship_line.shipping_date:
                proc_vals.update({
                    'date_planned': ship_line.shipping_date,
                    'date_deadline': ship_line.shipping_date})
            if ship_line.route_id:
                proc_vals.update({
                    'route_ids': ship_line.route_id})
            values.append(proc_vals)
        return values

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """Override the method  to update procurements values."""
        if self.ids and not self[0].order_id.split_shipment:
            return super(SaleOrderLine, self)._action_launch_stock_rule(
                previous_product_uom_qty)
        if self._context.get("skip_procurement"):
            return True
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        procurements = []
        shipping_lines = self.env['sale.multi.ship.qty.lines']
        for line in self:
            line = line.with_company(line.company_id)
            if line.state != 'sale' or \
                    not (line.product_id.type in ('consu', 'product')):
                continue
            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(
                    line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already
                # created and the order was
                # cancelled, we need to update certain values of
                # the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.\
                        partner_shipping_id:
                    updated_vals.update(
                        {'partner_id': line.order_id.
                         partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update(
                        {'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)

            # Date wise reserved the stock
            values = sorted(values, key=lambda d: d['date_planned'])
            for val in values:
                qty = val.get('ship_line').with_context(
                    rule=True)._get_qty_procurement(
                    previous_product_uom_qty)
                if float_compare(
                    qty, val.get('ship_line').product_qty,
                        precision_digits=precision) == 0:
                    continue
                shipping_lines += val.get('ship_line')
                product_qty = val.get('ship_line').product_qty - qty
                line_uom = line.product_uom
                quant_uom = line.product_id.uom_id
                product_qty, procurement_uom = line_uom._adjust_uom_quantities(
                    product_qty, quant_uom)
                procurements.append(self.env['procurement.group'].Procurement(
                    line.product_id, product_qty, procurement_uom,
                    line.order_id.partner_shipping_id.property_stock_customer,
                    line.name, line.order_id.name,
                    line.order_id.company_id, val))
        if procurements:
            self.env['procurement.group'].run(procurements)

        # This next block is currently needed only because the
        # scheduler trigger is done by picking confirmation rather
        # than stock.move confirmation
        orders = self.mapped('order_id')
        shipping_lines.write({'state': 'sale'})
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(
                lambda p: p.state not in ['cancel', 'done'])
            for pick in pickings_to_confirm:
                if pick.partner_id.id and pick.location_dest_id == pick.\
                        partner_id.property_stock_customer:
                    move_id = pick.mapped('move_ids_without_package')
                    delivery_id = pick.partner_id.\
                        property_delivery_carrier_id.id
                    if move_id:
                        delivery_ids = move_id.mapped('multi_ship_line_id')
                        delivery_id = delivery_ids[0].delivery_method_id.id
                    pick.carrier_id = delivery_id
            if pickings_to_confirm:
                # Trigger the Scheduler for Pickings
                pickings_to_confirm.action_confirm()
        return True

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Overide name_search for sale order line domain."""
        if not args:
            args = []
        if self.env.context.get('so_lines'):
            args += [('id', 'in', eval(self.env.context.get('so_lines')))]
        return super(SaleOrderLine, self).name_search(
            name, args, operator, limit)

    def name_get(self):
        """Updated display name."""
        res = []
        if self.env.context.get('multi_ship'):
            for sline in self:
                name = '[' + sline.product_id.default_code + '] ' + \
                    sline.product_id.name if sline.product_id.default_code else sline.product_id.name
                if sline.product_id.product_template_attribute_value_ids:
                    if sline.product_id.type == "consu":
                        variant_name = ", ".join([variant[:variant.find('(')] for variant in sline.product_id.product_template_attribute_value_ids.mapped('name')])
                        name = variant_name and "%s (%s) - %s" % (sline.product_id.name, variant_name, sline.product_qty) or sline.product_id.name
                    else:
                        name += "(" + ','.join(
                            sline.product_id.product_template_attribute_value_ids.
                            mapped('name')) + ")" + " - " + str(
                            sline.product_qty)
                else:
                    name += " - " + str(sline.product_qty)
                res.append((sline.id, name))
        else:
            res = super(SaleOrderLine, self).name_get()
        return res

    def write(self, values):
        """Overide method to update the edit qty logic."""
        lines = self.env['sale.order.line']
        if 'product_uom_qty' in values:
            lines = self.filtered(
                lambda r: r.state == 'sale' and not r.is_expense)
        previous_product_uom_qty = {line.id: line.product_uom_qty
                                    for line in lines}
        res = super(BaseSaleOrderLine, self).write(values)
        if lines:
            # if multi shipment true then need to create delivery
            # from shipping details.
            if not lines[0].order_id.split_shipment:
                lines._action_launch_stock_rule(previous_product_uom_qty)
        if 'customer_lead' in values and self.state == 'sale' and \
                not self.order_id.commitment_date:
            # Propagate deadline on related stock move
            # if multi shipment true then need to create delivery
            # from shipping details.
            if not lines[0].order_id.split_shipment:
                self.move_ids.date_deadline = self.order_id.date_order + \
                    timedelta(days=self.customer_lead or 0.0)
        return res

    @api.model
    def create(self, vals_list):
        """Skip create delvery when multi shipment is on."""
        lines = super(BaseSaleOrderLine, self).create(vals_list)
        if not lines.mapped('order_id').split_shipment:
            lines.filtered(
                lambda line: line.state == 'sale')._action_launch_stock_rule()
        for ship_line in lines:
            planned_qty = sum(ship_line.sale_multi_ship_qty_lines.filtered(
                lambda sl: sl.so_line_id.id == ship_line.id).mapped(
                'product_qty'))
            ship_line.update(
                {'remain_so_qty':
                    ship_line.product_uom_qty - planned_qty})
        return lines
