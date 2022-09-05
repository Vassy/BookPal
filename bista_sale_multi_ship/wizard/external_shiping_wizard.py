from datetime import datetime
import string
from odoo import api, fields, models


class ExternalShipping(models.TransientModel):
    _name = 'external.shipping'
    _description = 'External Shipping'

    date = fields.Datetime(string='Deadline', default=fields.Datetime.now)

    sale_id = fields.Many2one(
        'sale.order', string='Sale Id', default=lambda s: s._context.get('active_id'))
    partner_ids = fields.Many2many(
        'res.partner', 'external_shipping_id', 'partner_id', 'external_ship_partner_rel', string='Shipping Line')

    @api.model
    def default_get(self, fields):
        res = super(ExternalShipping, self).default_get(fields)
        context = dict(self.env.context)
        sale_obj = self.env['sale.order']
        if 'active_id' in context:
            sale_id = sale_obj.browse(context['active_id'])
            res['sale_id'] = sale_id.id
        return res

    # process external delivery for shipping
    def process_delivery_order(self):
        sale_multi_ship_qty_line_ids = self.partner_ids.mapped(
            'split_so_lines').ids
        self.sale_id.order_line.with_context(
            external_delivery=True,
            split_so_line=sale_multi_ship_qty_line_ids)._action_launch_stock_rule()
        return True
