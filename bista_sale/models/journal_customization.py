# -*- coding: utf-8 -*-
from odoo import _,api,fields, models


class JournalCustomization(models.Model):

    _name = 'journal.customization'
    _description = 'Journal Customization'


    name = fields.Char('Name')