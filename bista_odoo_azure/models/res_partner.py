from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    azuremodel_id = fields.Many2one("azure.models", string="Azure Key")
    emails_ids = fields.One2many('res.partner.email', 'partner_id', string='Optional Emails')

    @api.onchange('email')
    def onchange_email(self):
        res = super(ResPartner, self).onchange_email()
        final_list = self.emails_ids.ids
        for rec in self.emails_ids:
            if self.email and rec.self_email:
                rec.email = self.email
            elif not self.email and rec.self_email:
                final_list.remove(rec._origin.id)

        if any(self.emails_ids.filtered(lambda e: e.self_email)):
            self.emails_ids = [(6, 0, final_list)]
        else:
            self.emails_ids = [(0, 0, {
                'email': self.email,
                'self_email': True,
            })]

        return res


class ResPartnerEmails(models.Model):
    _name = "res.partner.email"
    _description = "Res Partner Email"

    email = fields.Char('Email')
    partner_id = fields.Many2one('res.partner', string='Partner')
    self_email = fields.Boolean('Self Partner Email', default=False)
