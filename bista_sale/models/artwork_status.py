# -*- coding: utf-8 -*-
from odoo import  _,api,fields, models


class ArtworkStatus(models.Model):

    _name = 'artwork.status'
    _description = 'Artwork Status'


    name = fields.Char('Name')