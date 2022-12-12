from odoo import fields, models, api

class AzureModels(models.Model):

    _name = "azure.models"
    _description = "Azure Keys"

    name = fields.Char("Azure Keyword", required=True)
    azure_model = fields.Char("Azure Models", required=True)


class DocumentsAzureLog(models.Model):

    _name = "documents.azure.log"
    _description = "Azure Log"

    name = fields.Char("Name")
    log = fields.Html("Log")


