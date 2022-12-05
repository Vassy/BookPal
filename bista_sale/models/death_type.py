# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DeathType(models.Model):
    _name = 'death.type'
    _description = 'Die Type'

    name = fields.Char('Name')
    active = fields.Boolean(string="Archived", default=True)

    def unlink(self):
        sale_orders = self.env['sale.order'].search([('death_type_id', '=', self.id)])
        if sale_orders:
            raise ValidationError('The record is existing in sale order you cannot delete the record, you can '
                                  'Archived it.')
        return super(DeathType, self).unlink()
