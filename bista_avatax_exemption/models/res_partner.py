
from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.constrains('tax_exempt_category')
    def update_tax_exemption_id(self):
        """Update exemption from big commerce."""
        for partner in self:
            if partner.tax_exempt_category:
                exemption_id = self.env['avatax.exemption'].sudo().search(
                    [('code', '=', partner.tax_exempt_category)])
                if not exemption_id:
                    exemption_id = self.env['avatax.exemption'].sudo().create(
                        {
                            'name': 'BC expexmption code',
                            'code': partner.tax_exempt_category,
                            'company_id': partner.company_id.id or
                            self.env.user.company_id.id
                        })
                partner.avalara_exemption_id = exemption_id.id

    @api.model
    def create(self, vals):
        """Update tax exemption when created customer from BC."""
        partner = super(ResPartner, self).create(vals)
        partner.update_tax_exemption_id()
        return partner
