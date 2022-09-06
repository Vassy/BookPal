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
                   'shipping_partner_id']
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
            res.update({
                'partner_id': values['ship_line'].partner_id.id,
                'date': values['ship_line'].shipping_date,
                'date_deadline': values['ship_line'].shipping_date,
            })
        elif values.get('move_dest_ids'):
            ship_line = values.get('move_dest_ids').mapped(
                'multi_ship_line_id')
            dest_move = values.get('move_dest_ids')[0]
            if ship_line:
                res.update({
                    'partner_id': ship_line.partner_id.id,
                    'date': ship_line.shipping_date,
                    'date_deadline': ship_line.shipping_date,
                })
            else:
                res.update({
                    'partner_id': dest_move.partner_id.id,
                    'date': dest_move.date,
                    'date_deadline': dest_move.date,
                })
        return res

    # I updated this logic in _prepare_procurement_values method
    # of sale order line becuase I want to add route before the rule
    # @api.model
    # def _run_pull(self, procurements):
    #     print ("\n self >>>>>>, self, procurements")
    #     # 8 / 0
    #     moves_values_by_company = defaultdict(list)
    #     mtso_products_by_locations = defaultdict(list)
    #     # To handle the `mts_else_mto` procure method, we do a
    #     # preliminary loop to isolate the products ]
    #     # we would need to read the forecasted quantity,
    #     # in order to to batch the read. We also make a sanitary check on the
    #     # `location_src_id` field.
    #     for procurement, rule in procurements:
    #         if procurement.values and 'sale_line_id' in procurement.values:
    #             so_line = self.env['sale.order.line'].browse(
    #                 procurement.values['sale_line_id'])
    #             if not so_line.order_id.split_shipment or not \
    #                     so_line.sale_multi_ship_qty_lines:
    #                 return super(StockRule, self)._run_pull(procurements)
    #         if not rule.location_src_id:
    #             msg = _('No source location defined on stock rule: %s!') % (
    #                 rule.name,)
    #             raise ProcurementException([(procurement, msg)])

    #         if rule.procure_method == 'mts_else_mto':
    #             mtso_products_by_locations[rule.location_src_id].append(
    #                 procurement.product_id.id)

    #     # Get the forecasted quantity for the `mts_else_mto` procurement.
    #     forecasted_qties_by_loc = {}
    #     for location, product_ids in mtso_products_by_locations.items():
    #         products = self.env['product.product'].browse(
    #             product_ids).with_context(location=location.id)
    #         forecasted_qties_by_loc[location] = {
    #             product.id: product.free_qty for product in products}

    #     # Prepare the move values, adapt the `procure_method` if needed.
    #     for procurement, rule in procurements:
    #         so_line = ''
    #         if procurement.values and 'sale_line_id' in procurement.values:
    #             so_line = self.env['sale.order.line'].browse(
    #                 procurement.values['sale_line_id'])

    #         procure_method = rule.procure_method
    #         if rule.procure_method == 'mts_else_mto':
    #             qty_needed = procurement.product_uom._compute_quantity(
    #                 procurement.product_qty,
    #                 procurement.product_id.uom_id)
    #             qty_available = forecasted_qties_by_loc[
    #                 rule.location_src_id][procurement.product_id.id]
    #             if float_compare(
    #                     qty_needed, qty_available,
    #                     precision_rounding=procurement.product_id.
    #                     uom_id.rounding) <= 0:
    #                 procure_method = 'make_to_stock'
    #                 forecasted_qties_by_loc[rule.location_src_id][
    #                     procurement.product_id.id] -= qty_needed
    #             else:
    #                 procure_method = 'make_to_order'
    #         if so_line:
    #             partner_shipping_id = so_line.order_id.partner_id
    #             split_qty_lines = so_line.sale_multi_ship_qty_lines.filtered(
    #                 lambda st: st.partner_id.state == 'verified')
    #             if self.env.context.get('external_delivery') and \
    #                     self.env.context.get('split_so_line'):
    #                 split_qty_lines = split_qty_lines.filtered(
    #                     lambda st: st.id in self.env.context.get(
    #                         'split_so_line'))
    #             for split_qty_line in split_qty_lines:
    #                 move_values = rule._get_stock_move_values(*procurement)
    #                 move_values['procure_method'] = procure_method
    #                 move_values['product_uom_qty'] = split_qty_line.\
    #                    product_qty
    #                 move_values['partner_id'] = split_qty_line.partner_id.id
    #                 move_values['shipping_partner_id'] = \
    #                   partner_shipping_id.id
    #                 # if ship_date:
    #                 move_values['date'] = split_qty_line.shipping_date
    #                 move_values['date_deadline'] = \
    #                    split_qty_line.shipping_date
    #                 move_values['sale_line_id'] = so_line.id
    #                 if split_qty_line.route_id:
    #                     move_values['route_ids'] = \
    #                        split_qty_line.route_id.id,
    #                 # move_values['route_ids'] = split_qty_line.route_id.id,
    #                 moves_values_by_company[
    #                     procurement.company_id.id].append(move_values)
    #         else:
    #             move_values = rule._get_stock_move_values(*procurement)
    #             move_values['procure_method'] = procure_method
    #             moves_values_by_company[
    #                 procurement.company_id.id].append(move_values)
    #             if 'move_dest_ids' in move_values and \
    #                     move_values['move_dest_ids']:
    #                 for dest_move in move_values['move_dest_ids']:
    #                     move_id = self.env['stock.move'].browse(dest_move[1])
    #                     if move_id.partner_id:
    #                         move_values['partner_id'] = move_id.partner_id.id
    #                         move_values[
    #                             'shipping_partner_id'] = move_id.\
    #                             shipping_partner_id.id
    #     for company_id, moves_values in moves_values_by_company.items():
    #         # create the move as SUPERUSER because the current user may not
    #         # have the rights to do it (mto product launched by a sale for
    #         # example)
    #         moves = self.env['stock.move'].with_user(
    #             SUPERUSER_ID).sudo().with_company(company_id).create(
    #             moves_values)
    #         # Since action_confirm launch following procurement_group
    #         # we should
    #         # activate it.
    #         moves._action_confirm()
    #         # set the Delivery Order in Multi ship lines to show DO and
    #         # Shipping reference in SO.
    #         for move_line in moves:
    #             if move_line.picking_id and move_line.partner_id:
    #                 move_line.partner_id.stock_picking_id = move_line.\
    #                     picking_id
    #     return True


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

    # def create(self, vals):
    #     print ("\n vals >>>>>.", vals.get('picking_type_id'))
    #     if vals.get('picking_type_id') == 7:
    #         3 / 0
    #     return super(StockPicking, self).create(vals)


class StockMove(models.Model):
    _inherit = 'stock.move'

    shipping_partner_id = fields.Many2one(
        'res.partner', string="Shipping Customer")
    multi_ship_line_id = fields.Many2one('sale.multi.ship.qty.lines', '')

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

    # @api.model
    # def create(self, vals):
    #     """Create."""
    #     print ("\n vals >>>>>.", vals)
    #     # 3 / 0
    #     return super(StockMove, self).create(vals)
