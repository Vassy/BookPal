# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ArtworkStatus(models.Model):
    _name = 'artwork.status'
    _description = 'Artwork Status'

    name = fields.Char('Name')
    active = fields.Boolean(string="Archived", default=True)

    def unlink(self):
        for rec in self:
            sale_orders = rec.env['sale.order'].search([('artwork_status_id', '=', rec.id)])
            if sale_orders:
                raise ValidationError('The record is existing in sale order you cannot delete the record, you can '
                                      'Archived it.')
            return super(ArtworkStatus, rec).unlink()
