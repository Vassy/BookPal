# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

import re

from odoo import models, api, fields, _

email_regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_international = fields.Boolean(string="Is International")

    @api.onchange('country_id')
    def _onchange_country_id(self):
        ctx = self._context
        if ctx.get('sale_id'):
            for rec in self:
                if rec.country_id and rec.country_id != rec.sale_id.company_id.country_id:
                    rec.is_international = True
                else:
                    rec.is_international = False

    def reset_to_draft(self):
        """Reset to draft."""
        for rec in self:
            rec.state = 'draft'

    @api.model
    def default_get(self, default_fields):
        """Default get."""
        values = super().default_get(default_fields)
        ctx = self._context
        vals = {}
        if ctx.get('sale_id'):
            sale_order = self.env['sale.order'].browse(ctx.get('sale_id'))
            val_lst = []
            if sale_order:
                multi_ship_id = sale_order.mapped(
                    'sale_multi_ship_qty_lines').mapped('multi_ship_id')
                if not multi_ship_id:
                    multi_ship_id = self.env['sale.multi.ship'].create(
                        {'sale_id': sale_order.id})
                values['multi_ship_id'] = multi_ship_id[0].id

                for order_line in sale_order.order_line.filtered(lambda line: line.product_id.detailed_type == 'product'):
                    consumed_qty = order_line.sale_multi_ship_qty_lines.mapped(
                        'product_qty')
                    line_product_qty = order_line.product_uom_qty
                    total_value = line_product_qty - sum(consumed_qty)
                    vals = {
                        'so_line_id': order_line.id, 'product_qty': total_value}
                    val_lst.append((0, 0, vals))

            if vals:
                values['split_so_lines'] = val_lst
                values['sale_id'] = sale_order.id
                values['country_id'] = False
        # if 'is_individual' in ctx and not ctx.get('is_individual'):
        #     print ("d >>>>>")
        #     values['parent_id'] = ctx.get('parent_id')
        return values

    def verify_customer_details(self):
        """Verify customer details."""
        for record in self:
            msg = ""
            verify_line = 'verified'
            if record.state != 'verified':

                if record.email and not re.search(email_regex, record.email):
                    verify_line = 'error'
                    msg += _("- Email format is not valid.\n")

                if not record.street:
                    verify_line = 'error'
                    msg += _("- Kindly enter Street Address.\n")

                if not record.property_delivery_carrier_id:
                    verify_line = 'error'
                    msg += _("- Kindly enter Delivery Method.\n")

                if not record.city:
                    verify_line = 'error'
                    msg += _("- Kindly enter City.\n")

                if not record.state_id:
                    verify_line = 'error'
                    msg += _("- Kindly enter State.\n")

                if not record.country_id:
                    verify_line = 'error'
                    msg += _("- Kindly enter Country.\n")

                if record.state_id.country_id.id != record.country_id.id:
                    verify_line = 'error'
                    msg += _("- Country not matching with State.\n")

                if record.split_so_lines:
                    for multi_ship_qty_line in record.split_so_lines:
                        if multi_ship_qty_line.product_qty <= 0:
                            verify_line = 'error'
                            prod_name = multi_ship_qty_line.product_id.name
                            if multi_ship_qty_line.product_id.product_template_attribute_value_ids:
                                prod_name += '(' + ','.join(
                                    multi_ship_qty_line.product_id.product_template_attribute_value_ids.mapped(
                                        'name')) + ')'
                            msg += _("- Product qty for %s must be more than 0.0.\n" % (prod_name))

            if verify_line:
                record.state = verify_line
            if msg:
                record.error_msg = msg
            if not record.multi_ship_id.partner_ids.filtered(lambda msl: msl.state != 'verified'):
                record.sale_id.ship_lines_validated = True
            else:
                record.sale_id.ship_lines_validated = False

    # New Added fields in Res Partner :
    is_multi_ship = fields.Boolean(string="Is Multi Ship")
    multi_ship_id = fields.Many2one('sale.multi.ship', string="Multi Ship Id")
    sale_id = fields.Many2one(
        'sale.order', related='multi_ship_id.sale_id', store=True)
    product_qty = fields.Float('Quantity', help="Quantity to Ship")
    attention = fields.Char('Attention', help="Attention")
    code = fields.Char(related="country_id.code", string="Code")
    split_so_lines = fields.One2many(
        'sale.multi.ship.qty.lines', 'partner_id', string="Split SO Lines")
    stock_picking_id = fields.Many2one(
        'stock.picking', string='Delivery Order Ref')
    carrier_track_ref = fields.Char(
        related="stock_picking_id.carrier_tracking_ref", help="Linked Tracking Reference")
    state = fields.Selection([('draft', 'Draft'), ('verified', 'Verified'), ('error', 'Error')], string='Status',
                             default='draft')
    error_msg = fields.Text(string='Error Message')

    carrier_ids = fields.Many2many(
        "delivery.carrier", compute='_get_delivery_type', string="Available Carriers")

    def _match_address(self, carrier):
        self.ensure_one()
        if carrier.country_ids and self.country_id not in carrier.country_ids:
            return False
        if carrier.state_ids and self.state_id not in carrier.state_ids:
            return False
        if carrier.zip_from and (self.zip or '').upper() < carrier.zip_from.upper():
            return False
        if carrier.zip_to and (self.zip or '').upper() > carrier.zip_to.upper():
            return False
        return True

    @api.depends('country_id', 'state_id', 'zip')
    def _get_delivery_type(self):
        for rec in self:
            # rec.property_delivery_carrier_id = False
            domain = ['|', ('company_id', '=', False),
                      ('company_id', '=', rec.sale_id.company_id.id)]
            if rec.sale_id.partner_carrier_id:
                domain.append(
                    ('delivery_type', '=', rec.sale_id.partner_carrier_id.delivery_type))
                if rec.sale_id.partner_carrier_id.ups_bill_my_account:
                    domain.append(
                        ('ups_bill_my_account', '=', True))
            else:
                domain.append(
                    ('ups_bill_my_account', '=', False))
            carriers = self.env['delivery.carrier'].search(domain)
            carriers = carriers.filtered(lambda c: rec._match_address(c))
            rec.carrier_ids = carriers

    @api.model
    def create(self, vals):
        """Create."""
        if vals.get('multi_ship_id') and not vals.get('phone'):
            company_phone = self.env.company.phone or self.env.company.mobile
            vals['phone'] = company_phone
        return super(ResPartner, self).create(vals)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """User can serach tax based on name and description."""
        if not args:
            args = []
        if not self.env.context.get('default_is_multi_ship'):
            args += [('is_multi_ship', '=', False)]
        ids = self._name_search(name, args, operator, limit=limit)
        return self.browse(ids).sudo().name_get()

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     if not args:
    #         args = []
    #     partner = self
    #     if self.ids:
    #         partner = self[0]
    #     # print ("\n partner >>1>>>>", partner)
    #     if self.env.context.get('is_multi_ship', False):
    #         args += [('is_multi_ship', '=', True)]
    #     elif partner and (partner.is_multi_ship or partner.parent_id.is_multi_ship):
    #         args += [('is_multi_ship', '=', True)]
    #     # elif len(args) == 1 and len(args[0]) == 3 and args[0][:2] == ('id', 'child_of') \
    #     #         and args[0][2] != [False]:
    #     #     partner = self.browse(args[0][2][0])
    #     #     if partner.is_multi_ship:
    #     #         args += [('is_multi_ship', '=', True)]
    #     #         print ("\n partner >>>2>", args[0][2])
    #     #     else:
    #     #         args += [('is_multi_ship', '=', False)]
    #     else:
    #         args += [('is_multi_ship', '=', False)]
    #     res = super(ResPartner, self).search(args, offset, limit, order, count)
    #     return res

    # @api.model
    # def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
    #     print ("\n search_read >>>>>>>>>", domain)
    #     # print ("\n self.env.context >>>>>>", self.env.context)

    #     # if self.env.context.get('is_multi_ship', False):
    #     #     domain = [('is_multi_ship', '=', True)]
    #     # # elif self.env.context.get('params', {}).get('view_type') == 'form':
    #     # #     args += [('is_multi_ship', '=', True)]
    #     # else:
    #     #     domain += [('is_multi_ship', '=', False)]

    #     # print ("\n args >>>>>w34", domain)
    #     return super(ResPartner, self).search_read(domain, fields, offset, limit, order)
