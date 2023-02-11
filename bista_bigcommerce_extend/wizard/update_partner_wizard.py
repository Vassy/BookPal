from odoo import fields, models


class UpdatePartnerWiz(models.TransientModel):
    _name = "update.partner.wiz"
    _description = "Update partner from BC"

    partner_ids = fields.Many2many(
        'res.partner', string="Customers",
        domain="[('bigcommerce_customer_id', '!=', False)]",
        default=lambda self: self._context.get('active_ids'))
    bigcommerce_store_ids = fields.Many2many(
        'bigcommerce.store.configuration',
        string="Bigcommerce Store", copy=False)

    def update_partner(self):
        """Update partner from bc."""
        for partner in self.partner_ids.filtered(
                lambda x: x.bigcommerce_customer_id):
            partner.with_context(
                customer_id=partner.bigcommerce_customer_id
            ).bigcommerce_to_odoo_import_customers(
                bigcommerce_store_ids=self.bigcommerce_store_ids)
