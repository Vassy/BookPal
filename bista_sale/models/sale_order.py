# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    white_glove_id = fields.Many2one(
        'white.glove.type', string='White Glove Type')
    event_date = fields.Date(string="Event Date")
    order_notes = fields.Text(string="Order Notes")
    product_status_notes = fields.Text(string="Product Status Notes")
    gorgias_ticket = fields.Text(string="Gorgias Ticket")
    ce_notes = fields.Text(string="CE Notes")
    payment_notes = fields.Text(string="Payment Notes")
    am_notes = fields.Text(string="AM Notes")
    ce_ops_acct_notes = fields.Text(string="CE-Ops Acct Notes")
    billing_notes = fields.Text(string="Billing Notes")
    placed_from_ip = fields.Char(string="Placed from IP")
    # journal or promotional product fields
    journal_customization_id = fields.Many2one(
        'journal.customization', string='Journal Customization')
    customization_cost = fields.Float('Our Customization Cost')
    link_to_art_files = fields.Text(string='Link to Art Files')
    artwork_status_id = fields.Many2one(
        'artwork.status', string='Artwork Status')
    journal_notes = fields.Text(string='Journal Notes')
    journal_setup_fee = fields.Char(string="Journal Set Up Fee")
    journal_setup_fee_waived = fields.Char(string="Journal Set Up Fee Waived")
    shipping_account = fields.Char(string="Shipping Account")
    shipping_cost = fields.Float(string=" Our Shipping Cost")
    death_type_id = fields.Many2one('death.type', string='Die Type')
    existing_death_order = fields.Char(string="Existing Death Order #")
    # Project & Fulfilment Tracking.
    fulfilment_project = fields.Boolean('Fulfilment Project')
    am_owner = fields.Char(string="AM Owner")
    project_description = fields.Char(string="Project Description")
    project_status = fields.Char(string="Project Status")
    status_notes = fields.Text(string='Status Notes')
    delivery_location = fields.Char(string="Delivery Location")
    shipping_instruction = fields.Text(string='Shipping Instruction')
    customization_type_ids = fields.Many2many(
        'customization.type', string="Customization Type")
    special_insert_note = fields.Text(string='Special Insert Notes')
    attachment_note = fields.Text(string='Attachment Notes')
    individual_mailer_return_receiver = fields.Char(
        string="Individual Mailer Return Receiver")
    recipient_list_status = fields.Char(string="Recipient List Status")
    recipient_list_expected = fields.Char(string="Recipient List Expected")
    individual_mailer_return_address = fields.Char(
        string="Individual Mailer Return Address")
    book_status = fields.Char(string="Book Status")
    on_hold_reason = fields.Text(string='On Hold Reason(s)')
    due_amount = fields.Monetary('Due Amount', related='partner_id.total_due')

    refer_by_company=fields.Char('Referring Organization')
    refer_by_person=fields.Char('Referring Person')
    account_order_standing=fields.Selection([
                                    ('high', 'High'),
                                    ('medium', 'Medium'),
                                    ('low', 'Low')],string='Account Order Standing')

    customer_email_add=fields.Char('Customer Email Address',related='partner_id.email')

    @api.depends('picking_ids.is_dropship')
    def _compute_picking_ids(self):
        super()._compute_picking_ids()
        for order in self:
            order.delivery_count = len(order.picking_ids.filtered(lambda p: p.picking_type_id.code in ['outgoing', 'internal'] and p.picking_type_id.sequence_code != 'INT'))

    def action_view_delivery(self):
        return self._get_action_view_picking(self.picking_ids.filtered(lambda p: not p.is_dropship and p.picking_type_id.code in ['outgoing', 'internal'] and p.picking_type_id.sequence_code != 'INT'))


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    tracking_ref = fields.Char(
        'Tracking Refrence', compute="get_tracking_ref")

    @api.depends('move_ids.state')
    def get_tracking_ref(self):
        """Get the tracking reference."""
        for line in self:
            tracking_ref = line.move_ids.filtered(
                lambda x: x.picking_type_id.code in
                ['outgoing', 'incoming'] and
                x.quantity_done).mapped(
                'picking_id').mapped('carrier_tracking_ref')
            tracking_ref = ', '.join([str(elem)
                                     for elem in tracking_ref if elem])
            line.tracking_ref = tracking_ref

    # def check_bo_transfer(self):
    #     name = ''
    #     if self.product_id:
    #         domain = [('picking_type_code', '=', 'incoming'),
    #                   ('partner_id', '=', self.product_id.seller_ids[0].name.id
    #                    if not self.supplier_id else self.supplier_id.id),
    #                   ('backorder_id', '!=', False),
    #                   ('state', 'not in', ['done', 'cancel'])]
    #         picking_ids = self.env['stock.picking'].search(domain)
    #         pick_id = picking_ids.move_ids_without_package.filtered(
    #             lambda x: x.product_id == self.product_id)
    #         if pick_id:
    #             for ref in pick_id:
    #                 name += '\n' + ref.picking_id.name
    #     return name

    # @api.onchange('product_id', 'supplier_id')
    # def onchange_product_vendor(self):
    #     result = {}
    #     bo_transfer = self.check_bo_transfer()
    #     if self.product_id and bo_transfer:
    #         message = _('"%s" Product is already in back order. you can check this backorder. %s')\
    #             % (self.product_id.display_name, bo_transfer)
    #         warning_mess = {
    #             'title': _('WARNING!'),
    #             'message': message
    #         }
    #         result = {'warning': warning_mess}
    #         return result


# class SaleMultiShipQtyLines(models.Model):
#     _inherit = "sale.multi.ship.qty.lines"
#     _description = 'Sale Multi Ship Qty Lines model details.'

#     def check_bo_transfer(self):
#         name = ''
#         if self.so_line_id:
#             domain = [('picking_type_code', '=', 'incoming'),
#                       ('partner_id', '=', self.so_line_id.product_id.seller_ids[0].name.id
#                        if not self.supplier_id else self.supplier_id.id),
#                       ('backorder_id', '!=', False),
#                       ('state', 'not in', ['done', 'cancel'])]
#             picking_ids = self.env['stock.picking'].search(domain)
#             pick_id = picking_ids.move_ids_without_package.filtered(
#                 lambda x: x.product_id == self.so_line_id.product_id)
#             if pick_id:
#                 for ref in pick_id:
#                     name += '\n' + ref.picking_id.name
#         return name

#     @api.onchange('so_line_id', 'supplier_id')
#     def onchange_product_vendor(self):
#         result = {}
#         bo_transfer = self.check_bo_transfer()
#         if self.so_line_id and bo_transfer:
#             message = _('"%s" Product is already in back order. you can check this backorder. %s')\
#                 % (self.so_line_id.product_id.display_name, bo_transfer)
#             warning_mess = {
#                 'title': _('WARNING!'),
#                 'message': message
#             }
#             result = {'warning': warning_mess}
#             return result
