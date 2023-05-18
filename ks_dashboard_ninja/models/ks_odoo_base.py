from odoo import models, fields, api, _


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model_create_multi
    def create(self, vals_list):
        recs = super(Base, self).create(vals_list)
        if 'ir.' not in self._name and self.env.user.has_group('base.group_user'):
            items = self.env['ks_dashboard_ninja.item'].search(
                [['ks_model_id.model', '=', self._name], ['ks_auto_update_type', '=', 'ks_live_update']])
            if items:
                online_partner = self.env['res.users'].search([]).filtered(lambda x: x.im_status == 'online').mapped(
                    "partner_id").ids
                """Added a loop to solve traceback when trying to Create multiple
                records, Which models are used in the Ninja Dashboard configuration"""
                for rec in recs:
                    updates = [[
                        (self._cr.dbname, 'res.partner', partner_id),
                        {'type': 'ks_dashboard_ninja.notification', 'changes': items.ids},
                        {'id': rec.id}
                    ] for partner_id in online_partner]
                    self.env['bus.bus']._sendmany(updates)
        return recs

    def write(self, vals):
        recs = super(Base, self).write(vals)
        if 'ir.' not in self._name and self.env.user.has_group('base.group_user'):
            items = self.env['ks_dashboard_ninja.item'].search(
                [['ks_model_id.model', '=', self._name], ['ks_auto_update_type', '=', 'ks_live_update']])
            if items:
                online_partner = self.env['res.users'].search([]).filtered(lambda x: x.im_status == 'online').mapped(
                    "partner_id").ids
                """Added a loop to solve traceback when trying to Update multiple
                records, Which models are used in the Ninja Dashboard configuration"""
                for rec in self:
                    updates = [[
                        (self._cr.dbname, 'res.partner', partner_id),
                        {'type': 'ks_dashboard_ninja.notification', 'changes': items.ids},
                        {'id': rec.id}
                    ] for partner_id in online_partner]
                    self.env['bus.bus']._sendmany(updates)
        return recs
