# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class JournalCustomization(models.Model):
    _name = 'journal.customization'
    _description = 'Journal Customization'

    name = fields.Char('Name')
    color = fields.Integer()
    active = fields.Boolean(string="Archived", default=True)

    def unlink(self):
        for rec in self:
            sale_orders = rec.env['sale.order'].search([('journal_customization_ids', '=', rec.id)])
            if sale_orders:
                raise ValidationError('The record is existing in sale order you cannot delete the record, you can '
                                      'Archived it.')
            return super(JournalCustomization, rec).unlink()
