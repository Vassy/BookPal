
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
                # search only child with same state
                same_state_child_partners = self.sudo().search(
                    [('parent_id', '=', partner.id),
                     ('state_id', '=', partner.state_id.id),
                     ])
                partners = same_state_child_partners | partner
                partners.sudo().write({
                    'avalara_exemption_id': exemption_id.id
                })
                # All search all childs
                child_partners = self.sudo().search(
                    [('parent_id', '=', partner.id),
                     ('avalara_partner_code', 'in', ['', False])
                     ])
                child_partners.write(
                    {'avalara_partner_code': partner.bigcommerce_customer_id})

    @api.constrains('bigcommerce_customer_id', 'child_ids', 'parent_id')
    def update_avalara_partner_code(self):
        """Update exemption from big commerce."""
        for partner in self:
            parent = self.env['res.partner']
            if partner.bigcommerce_customer_id:
                parent = partner
            elif partner.parent_id and \
                    partner.parent_id.bigcommerce_customer_id:
                parent = partner.parent_id
            child_partners = self.search(
                [('parent_id', '=', parent.id),
                 ('bigcommerce_customer_id', 'in', [False, '']),
                 ('avalara_partner_code', 'in', ['', False])])
            partners = child_partners | partner
            partners.sudo().write({
                'avalara_partner_code': parent.bigcommerce_customer_id,
            })
            for child in child_partners:
                if not child.tax_exempt_category and \
                        parent.state_id.id == child.state_id.id:
                    child.write(
                        {'tax_exempt_category': parent.tax_exempt_category
                         })

    @api.model
    def create(self, vals):
        """Update tax exemption when created customer from BC."""
        partner = super(ResPartner, self).create(vals)
        partner.update_tax_exemption_id()
        return partner
