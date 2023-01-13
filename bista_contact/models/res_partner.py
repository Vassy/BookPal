# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    type = fields.Selection(selection_add=[
        ('return', 'Return Address'),
        ('warehouse', 'Warehouse Address'), ]
    )
    # Contact Details
    customer_status = fields.Selection([('pending', 'Prospect'),
                                        ('active', 'Active'), ('idle', 'Idle'),
                                        ('churned', 'Churned'), ('dead', 'Dead'),
                                        ('supplier', 'Supplier')])
    dead_resone = fields.Char('Dead Reasone')
    dead_date = fields.Datetime('Dead Date')
    do_not_call = fields.Boolean('DO Not Call')
    email_opt_out = fields.Boolean(string="Email Opt Out", default=False)
    account_spend = fields.Float(string="Account Spend")

    # Important Details
    source = fields.Char('Source')
    referal_source = fields.Char('Referral Source')
    source_notes = fields.Char('Source Notes')
    product_order_count = fields.Integer('Product Sale' , compute="_compute_sale_product_count")
    product_purchase_count = fields.Integer('Product Purchase', compute="_compute_purchase_product_count")

    # Order Information
    avg_order_value = fields.Char('Average Order Value', compute='get_avg_order_value')
    first_order_date = fields.Datetime('First Order Date', compute='get_first_order_date')
    last_order_date = fields.Datetime('Last Order Date', compute='get_first_order_date')
    # sale_product_ids = fields.Many2many('product.product', string='Sale Products', compute='get_ordered_product')
    # purchase_product_ids = fields.Many2many('product.product', string='Purchase Products',
    #                                         compute='get_vendor_ordered_product')
    block_reason = fields.Char('Reason')
    block = fields.Boolean('Block')
    account_order_standing = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low')], string='Account Order Standing')

    def _compute_purchase_product_count(self):
        for partner_id in self:
            product_list = self.purchase_line_ids.filtered(
                lambda a: a.product_id.detailed_type != 'service').mapped('product_id').ids
            partner_id.product_purchase_count = len(product_list)

    def _compute_sale_product_count(self):
        for partner_id in self:
            product_list = self.sale_order_ids.mapped('order_line').filtered(
                lambda a: a.product_id.detailed_type != 'service').mapped('product_id').ids
            partner_id.product_order_count = len(product_list)

    def get_first_order_date(self):
        """To get first order date and last order date"""
        self.first_order_date = False
        self.last_order_date = False
        if self.sale_order_count > 0:
            date_list = self.sale_order_ids.mapped('date_order')
            date_list.sort()
            if date_list:
                self.first_order_date = date_list[0]
                self.last_order_date = date_list[-1]

    def get_avg_order_value(self):
        """To calculate average amount of customers's order"""
        self.avg_order_value = 0
        if self.sale_order_count > 0:
            amount = self.sale_order_ids.mapped('amount_total')
            self.avg_order_value = sum(amount) / self.sale_order_count

    def get_vendor_ordered_product(self):
        """To get Sale Products"""
        product_list = self.sale_order_ids.mapped('order_line').filtered(
            lambda a: a.product_id.detailed_type != 'service').mapped('product_id')
        val = [rec.id for rec in product_list]
        action = self.env.ref("product.product_normal_action_sell").read()[0]
        action['domain'] = [('id', 'in', val), ('active', 'in', (True, False))]
        return action

    def _avatar_get_placeholder_path(self):
        if self.type == 'return':
            return "bista_contact/static/img/return.jpg"
        if self.type == 'warehouse':
            return "bista_contact/static/img/warehouse.png"
        return super()._avatar_get_placeholder_path()

    def open_block_unblock_wizard(self):
        """ to block/unblock contact """
        partner_ids = self.ids
        if self.env.context.get('block'):
            return {
                'name': 'Details',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                "view_type": "form",
                'res_model': 'contact.status.update',
                'target': 'new',
                'view_id': self.env.ref
                ('bista_contact.customer_block_reasone_partner').id,
                'context': {'partner_ids': partner_ids, 'default_block': True},
            }
        if self.env.context.get('unblock'):
            return {
                'name': 'Details',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                "view_type": "form",
                'res_model': 'contact.status.update',
                'target': 'new',
                'view_id': self.env.ref
                ('bista_contact.customer_block_reasone_partner').id,
                'context': {'partner_ids': partner_ids, 'default_block': False},
            }

    def _get_name(self):
        """ Utility method to allow name_get to be overrided without re-browse the partner """
        partner = self
        name = partner.name or ''

        if partner.company_name or partner.parent_id:
            if not name and partner.type in ['invoice', 'delivery', 'other', 'return', 'warehouse']:
                name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
            if not partner.is_company:
                name = self._get_contact_name(partner, name)
        if self._context.get('show_address_only'):
            name = partner._display_address(without_company=True)
        if self._context.get('show_address'):
            name = name + "\n" + partner._display_address(without_company=True)
        name = name.replace('\n\n', '\n')
        name = name.replace('\n\n', '\n')
        if self._context.get('partner_show_db_id'):
            name = "%s (%s)" % (name, partner.id)
        if self._context.get('address_inline'):
            splitted_names = name.split("\n")
            name = ", ".join([n for n in splitted_names if n.strip()])
        if self._context.get('show_email') and partner.email:
            name = "%s <%s>" % (name, partner.email)
        if self._context.get('html_format'):
            name = name.replace('\n', '<br/>')
        if self._context.get('show_vat') and partner.vat:
            name = "%s ‒ %s" % (name, partner.vat)
        return name

    def get_vendor_purchased_product(self):
        """To get Purchased Products"""
        product_list = self.purchase_line_ids.filtered(
            lambda a: a.product_id.detailed_type != 'service').mapped('product_id')
        val = [rec.id for rec in product_list]
        action = self.env.ref("purchase.product_product_action").read()[0]
        action['domain'] = [('id', 'in', val), ('active', 'in', (True, False))]
        return action


