from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    azure_end_point = fields.Char("Azure End Point", readonly=False)
    azure_key = fields.Char("Azure Key", readonly=False)
    azure_model = fields.Char("Azure Model", readonly=False)
    re_read_mails = fields.Boolean("Re-Read Mails", default=False)
    azure_alias_domain = fields.Char('Azure Alias Domain')

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param("bista_odoo_azure.re_read_mails", self.re_read_mails)
        self.env['ir.config_parameter'].set_param("bista_odoo_azure.azure_alias_domain",
                                                  self.azure_alias_domain)
        self.env['ir.config_parameter'].set_param("bista_odoo_azure.azure_end_point", self.azure_end_point)
        self.env['ir.config_parameter'].set_param("bista_odoo_azure.azure_key",
                                                  self.azure_key)
        self.env['ir.config_parameter'].set_param("bista_odoo_azure.azure_model", self.azure_model)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        domain = self.env['ir.config_parameter'].sudo().get_param(
            'bista_odoo_azure.azure_alias_domain') or False
        azure_end_point = self.env['ir.config_parameter'].sudo().get_param(
            'bista_odoo_azure.azure_end_point') or False
        azure_key = self.env['ir.config_parameter'].sudo().get_param(
            'bista_odoo_azure.azure_key') or False
        azure_model = self.env['ir.config_parameter'].sudo().get_param(
            'bista_odoo_azure.azure_model') or False

        res.update(
            azure_alias_domain=domain,
            azure_end_point=azure_end_point,
            azure_key=azure_key,
            azure_model=azure_model,
        )
        return res
