##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, models, fields
from datetime import datetime


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(
        selection_add=[('customer_approved', 'Customer Approved'), ('min_price_review', 'Price Review'),
                       ('pending_for_approval', 'Pending for Approval'), ('approved', 'Approved'), ('sale',)])
    sale_approval_log_ids = fields.One2many(
        'sale.approval.log', 'sale_id', string="Approval Status")

    product_price_check = fields.Boolean(string='Is product price approved?', default=False)

    def write(self, vals):
        context = self._context
        if vals.get('state') and vals.get('state') == 'draft':
            vals.update({
                'product_price_check': False,
            })
        result = super(SaleOrder, self).write(vals)
        if vals.get('state') and vals.get('state') == 'sent':
            self._create_sale_approval_log(self.id, context.get('uid'), 'Quote Sent to Customer')
        return result

    def action_approve_minimum_price(self):
        for rec in self:
            rec.product_price_check = True
            context = self._context
            self._create_sale_approval_log(rec.id, context.get('uid'), 'Price Approved')
            action = rec.action_send_for_approval()
            if action:
                return action

    def action_send_for_approval(self):
        for rec in self:
            if rec.order_line and not rec.product_price_check:
                order_lines = []
                for order in rec.order_line.filtered(lambda o: o.product_id.minimum_sale_price):
                    if order.price_unit < order.product_id.minimum_sale_price:
                        order_lines.append(order.id)
                if len(order_lines) > 0:
                    return {
                        'name': 'Confirmation',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'res_model': 'min.price.wiz',
                        'view id': self.env.ref('bista_sales_approval.view_min_price_wiz_form').id,
                        'type': 'ir.actions.act_window',
                        'context': {'default_sale_id': self.id,
                                    'default_order_line_ids': order_lines,
                                    'minimum_price': False},
                        'target': 'new',
                    }

            rec.state = 'pending_for_approval'
            context = self._context
            self._create_sale_approval_log(rec.id, context.get('uid'), 'Quote Sent for Approval')

    def action_approval(self):
        for rec in self:
            rec.action_confirm()
            context = self._context
            self._create_sale_approval_log(rec.id, context.get('uid'), 'Approved')

    def action_reject(self):
        return {
            'name': 'Reject Reason',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'reject.reason.wiz',
            'view id': self.env.ref('bista_sales_approval.view_reject_reason_wiz_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_sale_id': self.id},
            'target': 'new',
        }

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        context = self._context
        self._create_sale_approval_log(self.id, context.get('uid'), 'Cancelled')
        return res

    @api.model
    def create(self, values):
        res = super(SaleOrder, self).create(values)
        self._create_sale_approval_log(res.id, res.create_uid.id, 'Quote Created')
        return res

    def _create_sale_approval_log(self, sale_id, create_id, action):
        self.env['sale.approval.log'].create({
            'sale_id': sale_id,
            'action_user_id': create_id,
            'done_action': action,
            'action_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    minimum_sale_price = fields.Float(string='Minimum Sale Price', related='product_id.minimum_sale_price')

    check_price_over_minimum = fields.Boolean('Check if Price Below Min', compute="_check_price_over_minimum")

    def _check_price_over_minimum(self):
        for rec in self:
            if rec.minimum_sale_price > rec.price_unit and rec.order_id.state == 'min_price_review':
                rec.check_price_over_minimum = True
            else:
                rec.check_price_over_minimum = False


class SaleApprovalLog(models.Model):
    _name = "sale.approval.log"
    _description = "Log information of Sale Order Approval Process"

    action_selection = [('created', 'Quote Created'),
                        ('send_for_price_review', 'Under Review for Minimum Price'),
                        ('credit_review', 'Credit Review'),
                        ('sent_to_customer', 'Quote Sent to Customer'),
                        ('sent_for_approval', 'Quote Sent for Approval'),
                        ('approved', 'Approved'),
                        ('rejected', 'Rejected'),
                        ('cancelled', 'Cancelled')]

    sale_id = fields.Many2one('sale.order')

    note = fields.Text(string='Reason')

    done_action = fields.Char(string="Performed Action")

    action_user_id = fields.Many2one('res.users', string='User')
    action_date = fields.Datetime(string='Date')
