# -*- coding: utf-8 -*-
from odoo import  _,api,fields, models


class WhiteGloveType(models.Model):

    _name = 'white.glove.type'
    _description = 'White Glove Type'


    code = fields.Char('Code Id')
    name = fields.Char('Name')
