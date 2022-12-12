from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    azure_end_point = fields.Char("Azure End Point", related="company_id.azure_end_point", readonly=False)
    azure_key = fields.Char("Azure Key", related="company_id.azure_key", readonly=False)
    azure_model = fields.Char("Azure Model", related="company_id.azure_model", readonly=False)
    re_read_mails = fields.Boolean("Re-Read Mails", defaul=False)
    azure_alias_domain = fields.Char('Azure Alias Domain')

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param("bista_odoo_azure.re_read_mails", self.re_read_mails)
        self.env['ir.config_parameter'].set_param("bista_odoo_azure.azure_alias_domain",
                                                  self.azure_alias_domain)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        domain = self.env['ir.config_parameter'].sudo().get_param(
            'bista_odoo_azure.azure_alias_domain') or False
        res.update(
            azure_alias_domain=domain,
        )
        return res
