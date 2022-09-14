# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from datetime import timedelta
# from collections import defaultdict
from itertools import groupby

from odoo import _, api, fields, models
# from odoo.addons.stock.models.stock_rule import ProcurementException
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += ['sale_line_id', 'partner_id',
                   'shipping_partner_id', 'multi_ship_line_id']
        return fields

    def _get_stock_move_values(self, product_id, product_qty,
                               product_uom, location_id, name, origin,
                               company_id, values):
        res = super(StockRule, self)._get_stock_move_values(
            product_id, product_qty, product_uom,
            location_id, name, origin, company_id, values)
        # import pdb
        # pdb.set_trace()
        if values.get('ship_line'):
            if values.get('ship_line').shipping_date:
                res.update({
                    'date': values['ship_line'].shipping_date,
                    'date_deadline': values['ship_line'].shipping_date})
            res.update({
                'partner_id': values['ship_line'].partner_id.id,
            })
        elif values.get('move_dest_ids'):
            ship_line = values.get('move_dest_ids').mapped(
                'multi_ship_line_id')
            dest_move = values.get('move_dest_ids')[0]
            if ship_line:
                if ship_line.shipping_date:
                    res.update({
                        'date': ship_line.shipping_date,
                        'date_deadline': ship_line.shipping_date})
                res.update({
                    'partner_id': ship_line.partner_id.id,
                })
            else:
                res.update({
                    'partner_id': dest_move.partner_id.id,
                    'date': dest_move.date,
                    'date_deadline': dest_move.date,
                })
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    third_party_shipper = fields.Char(
        related="sale_id.third_party_shipper")

    ups_bill_my_account = fields.Boolean(
        related='carrier_id.ups_bill_my_account',
        readonly=True)

    shipping_partner_id = fields.Many2one(
        'res.partner', string="Customer")

    def action_automatic_entry(self):
        action = self.env.ref(
            'bista_sale_multi_ship.action_put_in_pack_wizard').sudo().read()[0]

        for picking in self:
            if not picking.carrier_id:
                raise ValidationError(
                    _("Set carrier for each selected record."))

        picking_carriers = self.mapped('carrier_id')
        carrier_type_list = picking_carriers.mapped('delivery_type')
        is_equal = all(
            dt.name == picking_carriers[0].name for dt in picking_carriers)
        if not is_equal:
            raise ValidationError(_("Select records with similar carrier."))

        # Force the values of the move line in the context to avoid issues
        ctx = dict(self.env.context)
        ctx.pop('active_id', None)
        ctx['active_ids'] = self.ids
        ctx['active_model'] = 'stock.picking'
        ctx['carrier_type_list'] = carrier_type_list or []
        action['context'] = ctx
        return action


class StockMove(models.Model):
    _inherit = 'stock.move'

    shipping_partner_id = fields.Many2one(
        'res.partner', string="Shipping Customer")
    multi_ship_line_id = fields.Many2one(
        'sale.multi.ship.qty.lines', 'Multi Shipments')

    def _get_new_picking_values(self):
        """_get_new_picking_values.

        return create values for new picking that will be linked with group
        of moves in self.
        """
        res = super(StockMove, self)._get_new_picking_values()
        res.update(
            {'shipping_partner_id': self.mapped('shipping_partner_id').id})
        if self.picking_type_id and \
            self.picking_type_id.code == 'outgoing' and \
            'carrier_id' in res and not \
                res.get('carrier_id') and \
            self.group_id and self.group_id.sale_id and \
                self.group_id.sale_id.carrier_id:
            res.update({'carrier_id': self.group_id.sale_id.carrier_id.id})
        if self.partner_id and self.picking_type_id.code == 'outgoing' \
                and not res.get('carrier_id', False):
            res.update({
                'carrier_id': self.partner_id.property_delivery_carrier_id.id})
        if self.picking_type_id.code == 'outgoing' and (
                not self.partner_id and
                self.group_id.sale_id.return_label_on_delivery_so):
            res.update({'return_label_on_delivery_picking': True})
        return res

    def _key_assign_picking(self):
        """Added partner and date based on that create picking."""
        self.ensure_one()
        res = super(StockMove, self)._key_assign_picking()
        if not self.group_id.sale_id.split_shipment:
            return res
        if self.partner_id not in res:
            res += (self.partner_id, self.date)
        return res

    def _search_picking_for_assignation_domain(self):
        """Added domain for partner and date."""
        domain = super(StockMove, self).\
            _search_picking_for_assignation_domain()
        if not self.group_id.sale_id.split_shipment:
            return domain
        if self.partner_id:
            domain += [('partner_id', '=', self.partner_id.id)]
        if self.date:
            st_date = fields.Datetime.to_string(self.date)
            en_date = fields.Datetime.to_string(self.date + timedelta(days=1))
            domain += [('scheduled_date', '>=', st_date),
                       ('scheduled_date', '<', en_date)]
        return domain

    def _assign_picking(self):
        """Overide method to add group by partner, date and routes."""
        if not self.group_id.sale_id.split_shipment:
            return super(StockMove, self)._assign_picking()
        pick_obj = self.env['stock.picking']
        grouped_moves = groupby(
            sorted(
                self,
                key=lambda m: [f if isinstance(
                    f, fields.datetime) else
                    f.id for f in m._key_assign_picking()]),
            key=lambda m: [m._key_assign_picking()])
        for group, moves in grouped_moves:
            moves = self.env['stock.move'].concat(*list(moves))
            new_picking = False
            # Could pass the arguments contained in group but they are the same
            # for each move that why moves[0] is acceptable
            picking = moves[0]._search_picking_for_assignation()
            if picking:
                # If a picking is found, we'll append `move` to its move list
                # and thus its
                # `partner_id` and `ref` field will refer to multiple records.
                # In this case, we chose to wipe them.
                vals = {}
                if any(picking.partner_id.id !=
                        m.partner_id.id for m in moves):
                    vals['partner_id'] = False
                if any(picking.origin != m.origin for m in moves):
                    vals['origin'] = False
                if vals:
                    picking.write(vals)
            else:
                # Don't create picking for negative moves since they will be
                # reverse and assign to another picking
                moves = moves.filtered(lambda m: float_compare(
                    m.product_uom_qty, 0.0,
                    precision_rounding=m.product_uom.rounding) >= 0)
                if not moves:
                    continue
                new_picking = True
                picking = pick_obj.create(moves._get_new_picking_values())

            moves.write({'picking_id': picking.id})
            moves._assign_picking_post_process(new=new_picking)
        return True

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self).\
            _prepare_merge_moves_distinct_fields()
        distinct_fields.append('multi_ship_line_id')
        return distinct_fields


class PurchaseOrderLine(models.Model):
    """Overided due to update shipping line reference in dropship move."""

    _inherit = "purchase.order.line"

    multi_ship_line_id = fields.Many2one(
        'sale.multi.ship.qty.lines', 'Shipment Lines')

    @api.model
    def _prepare_purchase_order_line_from_procurement(
            self, product_id, product_qty, product_uom, company_id,
            values, po):
        """Update shipping line value."""
        res = super(PurchaseOrderLine, self).\
            _prepare_purchase_order_line_from_procurement(
                product_id, product_qty, product_uom,
                company_id, values, po)
        if values.get('ship_line'):
            res.update({'multi_ship_line_id': values.get('ship_line').id})
        return res

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty,
                                 product_uom):
        self.ensure_one()
        self._check_orderpoint_picking_type()
        res = super(PurchaseOrderLine, self)._prepare_stock_move_vals(
            picking, price_unit, product_uom_qty, product_uom)
        if self.multi_ship_line_id:
            res.update({'multi_ship_line_id': self.multi_ship_line_id.id})
        return res
