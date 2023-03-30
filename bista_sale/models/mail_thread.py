from odoo import models, _, api
# from lxml import html
# import html



class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'


    def _notify_classify_recipients(self, recipient_data, model_name, msg_vals=None):
        """ Classify recipients to be notified of a message in groups to have
        specific rendering depending on their group. For example users could
        have access to buttons customers should not have in their emails.
        Module-specific grouping should be done by overriding ``_notify_get_groups``
        method defined here-under.
        :param recipient_data:todo xdo UPDATE ME
        return example:
        [{
            'actions': [],
            'button_access': {'title': 'View Simple Chatter Model',
                                'url': '/mail/view?model=mail.test.simple&res_id=1497'},
            'has_button_access': False,
            'recipients': [11]
        },
        {
            'actions': [],
            'button_access': {'title': 'View Simple Chatter Model',
                            'url': '/mail/view?model=mail.test.simple&res_id=1497'},
            'has_button_access': False,
            'recipients': [4, 5, 6]
        },
        {
            'actions': [],
            'button_access': {'title': 'View Simple Chatter Model',
                                'url': '/mail/view?model=mail.test.simple&res_id=1497'},
            'has_button_access': True,
            'recipients': [10, 11, 12]
        }]
        only return groups with recipients
        """
        # keep a local copy of msg_vals as it may be modified to include more information about groups or links
        local_msg_vals = dict(msg_vals) if msg_vals else {}
        groups = self._notify_get_groups(msg_vals=local_msg_vals)
        access_link = self._notify_get_action_link('view', **local_msg_vals)
        if model_name:
            view_title = _('View %s', model_name)
        if model_name in ["Sales", "Sales Order"]:
            view_title = _('See %s', local_msg_vals.get('record_name'))
        else:
            view_title = _('View')
        # fill group_data with default_values if they are not complete
        for group_name, group_func, group_data in groups:
            group_data.setdefault('notification_group_name', group_name)
            group_data.setdefault('notification_is_customer', False)
            is_thread_notification = self._notify_get_recipients_thread_info(msg_vals=msg_vals)['is_thread_notification']
            group_data.setdefault('has_button_access', is_thread_notification)
            group_button_access = group_data.setdefault('button_access', {})
            group_button_access.setdefault('url', access_link)
            group_button_access.setdefault('title', view_title)
            group_data.setdefault('actions', list())
            group_data.setdefault('recipients', list())

        # classify recipients in each group
        for recipient in recipient_data:
            for group_name, group_func, group_data in groups:
                if group_func(recipient):
                    group_data['recipients'].append(recipient['id'])
                    break

        result = []
        for group_name, group_method, group_data in groups:
            if group_data['recipients']:
                result.append(group_data)
        return result

class Followers(models.Model):
    """ mail_followers holds the data related to the follow mechanism inside
    Odoo. Partners can choose to follow documents (records) of any kind
    that inherits from mail.thread. Following documents allow to receive
    notifications for new messages. A subscription is characterized by:

    :param: res_model: model of the followed objects
    :param: res_id: ID of resource (may be 0 for every objects)
    """
    _inherit = 'mail.followers'

    def _add_followers(self, res_model, res_ids, partner_ids, subtypes,
                       check_existing=False, existing_policy='skip'):
        record = self.env[res_model].browse(res_ids[0])
        if record and record.create_uid.partner_id and not self._context.get('from_add_followers'):
            for partner in partner_ids:
                if partner != record.create_uid.partner_id.id:
                    partner_ids.remove(partner)
        res = super()._add_followers(res_model, res_ids, partner_ids, subtypes, check_existing, existing_policy)
        return res
