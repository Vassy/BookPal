from odoo import fields, models, api


class DocumentShare(models.Model):
    _inherit = "documents.share"

    filter_mail = fields.Boolean("Filter Mail")
    filter_type_selection = fields.Selection(string='Filter by',
                                             selection=[('sender', 'Filter By Sender'),
                                                        # ('attachment', 'Filter By Attachment'),
                                                        ('keyword', 'Filter By Keyword')])
    filter_attachments = fields.One2many("documents.share.filter", "share_id")
    filter_keywords = fields.One2many("documents.share.filter", "share_id")


class DocumentShareFilter(models.Model):
    _name = "documents.share.filter"
    _description = "Share Filter"

    filter_name = fields.Char("Filter Value")
    share_id = fields.Many2one("documents.share", string="Share")


class Alias(models.Model):
    _inherit = "mail.alias"

    # def _default_alias_domain(self):
    #     res = super(Alias, self)._default_alias_domain()
    #     context = self._context
    #     if context.get('install_xmlid'):
    #         if context.get('install_xmlid') == 'share_azure_fetch_link':
    #             return self.env['ir.config_parameter'].sudo().get_param(
    #                 'bista_odoo_azure.azure_alias_domain') or res
    #     return res

    def _compute_alias_domain(self):
        alias_domain = self.env["ir.config_parameter"].sudo().get_param("mail.catchall.domain")
        for record in self:
            if record.alias_parent_model_id.model == 'documents.share' and record.alias_parent_thread_id == self.env.ref(
                    'bista_odoo_azure.share_azure_fetch_link').id:
                record.alias_domain = self.env['ir.config_parameter'].sudo().get_param(
                    'bista_odoo_azure.azure_alias_domain') or alias_domain
            else:
                record.alias_domain = alias_domain
