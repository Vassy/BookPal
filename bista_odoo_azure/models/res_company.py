
from odoo import fields, models, api

class ResCompany(models.Model):

    _inherit = "res.company"

    azure_end_point = fields.Char("Azure End Point")
    azure_key = fields.Char("Azure Key")
    azure_model = fields.Char("Azure Model")