# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _description = "Sale Order Line Description"

    remaining_qty = fields.Float('Remaining Qty',
                                 compute="_calculate_remain_order_status_qty",
                                 compute_sudo=True)
    order_status = fields.Selection(
        [('pending', 'Pending'), ('completed', 'Completed')],
        compute="_calculate_remain_order_status_qty",
        string="SO Order Status", store=True, compute_sudo=True)
    order_po_ref = fields.Char(related="order_id.client_order_ref", store=True)
    so_date = fields.Datetime(related="order_id.date_order", store=True)
    partner_country = fields.Many2one('res.country', string="Country",
                                      related="order_partner_id.country_id",
                                      store=True)
    partner_state = fields.Many2one('res.country.state', string="State",
                                    related="order_partner_id.state_id",
                                    store=True)
    so_invoice_status = fields.Selection(string='SO Invoice Status',
                                         related="order_id.invoice_status",
                                         store=True, readonly=True)
    qty_shortclose = fields.Float('Short Close Qty/ Refund Qty',
                                  compute='_compute_qty_backorder_shortclose'
                                  , digits='Product Unit of Measure',
                                  store=True, compute_sudo=True)
    delivery_value = fields.Float(string="Delivery Value",
                                  compute='_compute_qty_backorder_shortclose',
                                  compute_sudo=True)
    short_close_value = fields.Float(string="Short Close/ Refund Value",
                                     compute='_compute_qty_backorder_shortclose',
                                     compute_sudo=True)
    pending_value = fields.Float(string="Pending Value",
                                 compute='_calculate_remain_order_status_qty',
                                 compute_sudo=True)
    order_expected_date = fields.Datetime(related="order_id.expected_date",
                                          store=True)
    product_onhand_qty = fields.Float("On Hand Qty",
                                      compute="current_product_onhand_qty")
    refund_qty = fields.Float("Refund Qty",
                              compute="compute_refund_invoice_qty")
    industry_id = fields.Many2one('res.partner.industry',
                                    related="order_partner_id.industry_id",
                                    store=True)

    def get_return_quantity(self):
        for sline in self:
            return_pickings = sline.order_id.picking_ids.filtered(
                lambda x: x.origin and "Return of" in x.origin
            )
            return_lines = return_pickings.move_ids_without_package.filtered(
                lambda x: x.product_id == sline.product_id and x.state in (
                    'done'))
            return_lines_qty = sum(
                return_lines.mapped('quantity_done')) if \
                return_lines else 0.0
            return return_lines_qty or 0.0

    @api.depends('qty_invoiced')
    def compute_refund_invoice_qty(self):
        for saleline in self:
            refund_qty_invoiced = 0.0
            for invoice_line in saleline._get_invoice_lines():
                if invoice_line.move_id.state != 'cancel':
                    if invoice_line.move_id.move_type == 'out_refund':
                        refund_qty_invoiced -= \
                            invoice_line.product_uom_id._compute_quantity(
                                invoice_line.quantity, saleline.product_uom)
            saleline.refund_qty = refund_qty_invoiced

    @api.depends('product_id', 'order_status', 'state')
    def current_product_onhand_qty(self):
        for prod in self:
            prod_qty_available = 0.0
            res = prod.product_id._compute_quantities_dict(
                self._context.get('lot_id'),
                self._context.get('owner_id'),
                self._context.get('package_id'),
                self._context.get('from_date'),
                self._context.get('to_date'))
            line_product_id = prod.product_id.id
            if line_product_id and res[line_product_id] and res[
                line_product_id].get('qty_available'):
                prod_qty_available = res[line_product_id].get('qty_available')
            if prod.product_id and prod.product_id.qty_available \
                and prod.order_status == 'pending':
                prod.product_onhand_qty = prod_qty_available
            else:
                prod.product_onhand_qty = 0.0

    @api.depends('order_id.picking_ids', 'qty_delivered', 'refund_qty',
                 'remaining_qty')
    def _compute_qty_backorder_shortclose(self):
        for line in self:
            if line.order_id.picking_ids:
                # for shortclose qty
                pickings = line.order_id.picking_ids.filtered(
                    lambda
                        x: x.picking_type_id.sequence_code == 'OUT' and not
                    x.backorder_id)
                backorder_pickings = line.order_id.picking_ids.filtered(
                    lambda
                        x: x.picking_type_id.sequence_code == 'OUT' and
                           x.backorder_id)
                pickings |= backorder_pickings

                noback_move_lines = pickings.move_ids_without_package.filtered(
                    lambda x: x.product_id == line.product_id and x.sale_line_id.id == line.id and x.state in (
                        'cancel') and x.picking_id.state != 'cancel')
                shortclose_qty = sum(
                    noback_move_lines.mapped('product_uom_qty')) if \
                    noback_move_lines else 0.0
                line.qty_shortclose = shortclose_qty
                line.delivery_value = line.qty_delivered * line.discounted_price
                line.short_close_value = line.qty_shortclose * line.discounted_price
                if (abs(line.refund_qty) + line.qty_delivered +
                    line.qty_shortclose) == line.product_uom_qty or abs(
                    line.refund_qty) > 0:
                    line.qty_shortclose += abs(line.refund_qty)
                    line.short_close_value = line.qty_shortclose * \
                                             line.discounted_price
            else:
                line.qty_shortclose = 0.0
                line.delivery_value = line.short_close_value = 0.0

    @api.depends('product_uom_qty', 'qty_delivered',
                 'refund_qty')
    def _calculate_remain_order_status_qty(self):
        for rec in self:
            returnqty = self.get_return_quantity()
            rec.remaining_qty = (rec.product_uom_qty - rec.qty_delivered) - rec.qty_shortclose
            rec.pending_value = rec.remaining_qty * rec.discounted_price or 0.0
            # if rec.qty_delivered + rec.remaining_qty >= rec.product_uom_qty:
            #     rec.order_status = 'pending'
            # if returnqty == abs(rec.refund_qty):
            #     rec.order_status = 'completed'
            # if rec.product_uom_qty == rec.qty_delivered:
            #     rec.order_status = 'completed'
            if rec.remaining_qty:
                rec.order_status = 'pending'
            else:
                rec.order_status = 'completed'

            # if rec.qty_delivered == rec.qty_invoiced and (rec.remaining_qty and rec.qty_shortclose):
            #     rec.qty_shortclose += rec.remaining_qty
            #     rec.remaining_qty = 0.0

