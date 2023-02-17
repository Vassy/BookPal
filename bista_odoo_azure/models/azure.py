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


class AutomatedPurchaseTracking(models.Model):

    _name = "automated.purchase.tracking.log"
    _description = "Purchase Trackings"
    _rec_name = "document_id"

    order_id = fields.Many2one('purchase.order', string='PO', default=False)
    tracking_number_id = fields.Many2one('purchase.tracking', string='Tracking Number', default=False)
    document_id = fields.Many2one('documents.document', string='Document',default=False)
    status = fields.Selection([('done', 'Done'),
                                        ('failed', 'Failed')])
    reason = fields.Text('Reason')



