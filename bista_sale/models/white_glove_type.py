# -*- coding: utf-8 -*-
from odoo import fields, models


class WhiteGloveType(models.Model):

    _name = 'white.glove.type'
    _description = 'White Glove Type'

    code = fields.Char('Code Id')
    name = fields.Char('Name')

    _sql_constraints = [
        ('code_glove_uniq', 'unique (code)',
         'White Glove Type Code has to be unique !')
    ]
