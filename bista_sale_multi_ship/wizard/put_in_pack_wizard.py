# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class PutInPackWizard(models.TransientModel):
    _name = 'put.in.pack.wizard'
    _description = 'Put In Pack Wizard'

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get('active_ids'):
            active_ids = self.env.context.get('active_ids')
            if active_ids:
                stock_pickings = self.env['stock.picking'].browse(active_ids)
                defaults['picking_ids'] = stock_pickings
        return defaults

    package_type = fields.Many2one('stock.package.type', 'Package Type', check_company=True)
    shipping_weight = fields.Float('Shipping Weight')
    weight_uom_name = fields.Char(string='Weight unit of measure label', compute='_compute_weight_uom_name')
    company_id = fields.Many2one('res.company', string="Company Id")
    picking_ids = fields.Many2many('stock.picking', string='Picking Ids')

    @api.depends('package_type')
    def _compute_weight_uom_name(self):
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        for record in self:
            record.weight_uom_name = weight_uom_id.name

    @api.onchange('package_type')
    def _onchange_package_type(self):
        if self.package_type:
            self.shipping_weight = 0

    @api.onchange('package_type', 'shipping_weight')
    def _onchange_package_type_weight(self):
        if self.package_type.max_weight and self.shipping_weight > self.package_type.max_weight:
            self.shipping_weight = 0
            warning_mess = {
                'title': _('Package too heavy!'),
                'message': _(
                    'The weight of your package is higher than the maximum weight authorized for this package type. Please choose another package type.')
            }
            return {'warning': warning_mess}

    def action_put_in_pack(self):
        if not self.package_type:
            raise UserError(_("Please add Delivery Package Type."))
        if not self.shipping_weight:
            raise UserError(_("Please add Shipping Weight."))

        if not all(self.package_type.package_carrier_type == picking.carrier_id.delivery_type for picking in
                   self.picking_ids):
            raise UserError(
                _("Select proper package type compatible with shipping carrier selected in delivery orders. \nThere might be orders with different shipping carrier are selected."))

        for picking_id in self.picking_ids:
            picking_move_lines = picking_id.move_line_ids
            if not picking_id.picking_type_id.show_reserved and not self.env.context.get('barcode_view'):
                picking_move_lines = picking_id.move_line_nosuggest_ids

            move_line_ids = picking_move_lines.filtered(lambda ml:
                                                        float_compare(ml.qty_done, 0.0,
                                                                      precision_rounding=ml.product_uom_id.rounding) > 0
                                                        and not ml.result_package_id
                                                        )
            if not move_line_ids:
                move_line_ids = picking_move_lines.filtered(lambda ml: float_compare(ml.product_uom_qty, 0.0,
                                                                                     precision_rounding=ml.product_uom_id.rounding) > 0 and float_compare(
                    ml.qty_done, 0.0,
                    precision_rounding=ml.product_uom_id.rounding) == 0)
            if move_line_ids:
                delivery_package = picking_id._put_in_pack(move_line_ids)
                # write shipping weight and package type on 'stock_quant_package' if needed
                if self.package_type:
                    delivery_package.package_type_id = self.package_type
                if self.shipping_weight:
                    delivery_package.shipping_weight = self.shipping_weight
