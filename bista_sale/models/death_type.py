# -*- coding: utf-8 -*-
from odoo import  _,api,fields, models


class ArtworkStatus(models.Model):

    _name = 'death.type'
    _description = 'Death Type'


    name = fields.Char('Name')