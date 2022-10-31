from odoo import fields, models, api, _


class UpdateShipping(models.TransientModel):
    _name = 'update.shipping'
    _description = 'Update Shipping'

    order_id=fields.Many2one('purchase.order')
    po_lines=fields.Many2many('purchase.order.line',string='Purchase Line')
    status = fields.Selection([('draft', 'Draft'),
                               ('ready_for_preview', 'Ready For Preview '),
                               ('ordered', 'Ordered '),
                               ('pending', 'Pending/In Transint'),
                               ('received', 'Received'),
                               ('stocked', 'Stocked'),
                               ('completed', 'Completed'),
                               ('return_created', 'Return created'),
                               ('rush_ordered', 'Rush Ordered'),
                               ('on_hold', 'On Hold'),
                               ('canceled', 'Canceled'),
                               ('invoiced', 'Invoiced'),
                               ('partially_received', 'Partially Received')], force_save="1")

    def update(self):
        for line in self.po_lines:
            for purchase in line.order_id.order_line:
                print('purchase', purchase, purchase.id)
                if purchase.id == line.id:
                    purchase.status = self.status
