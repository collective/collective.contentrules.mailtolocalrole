from Acquisition import aq_inner
from OFS.SimpleItem import SimpleItem
from zope.component import adapts
from zope.component.interfaces import ComponentLookupError
from zope.interface import Interface, implements
from zope.formlib import form
from zope import schema

from plone.app.contentrules.browser.formhelper import AddForm, EditForm
from plone.contentrules.rule.interfaces import IRuleElementData, IExecutable

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode

# import the default messagefactory as _plone. These strings will not be put in
# the locales .po file by i18ndude
from Products.CMFPlone import PloneMessageFactory as _plone
from collective.contentrules.mailtolocalrole import \
    mailtolocalroleMessageFactory as _


class IMailLocalRoleAction(Interface):
    """Definition of the configuration available for a mail action
    """
    subject = schema.TextLine(
        title=_plone(u"Subject"),
        description=_plone(u"Subject of the message"),
        required=True)
    source = schema.TextLine(
        title=_plone(u"Email source"),
        description=_plone("The email address that sends the \
email. If no email is provided here, it will use the portal from address."),
        required=False)
    localrole = schema.Choice(
        title=_(u"Local Role"),
        description=_("Select a local role. \
The action will look up the all Plone site users who explicitly have this \
local role on the object and send a message to their email address."),
        vocabulary="collective.contentrules.mailtolocalrole.local_roles",
        required=True)
    acquired = schema.Bool(
        title=_(u"Acquired Roles"),
        description=_("Should users that have this \
role as an acquired role also receive this email?"),
        required=False)
    message = schema.Text(
        title=_plone(u"Message"),
        description=_plone(u"Type in here the message that you \
want to mail. Some defined content can be replaced: ${title} will be replaced \
by the title of the newly created item. ${url} will be replaced by the \
URL of the newly created item."),
        required=True)


class MailLocalRoleAction(SimpleItem):
    """
    The implementation of the action defined before
    """
    implements(IMailLocalRoleAction, IRuleElementData)

    subject = u''
    source = u''
    localrole = u''
    message = u''
    acquired = False
    element = 'plone.actions.MailLocalRole'

    @property
    def summary(self):
        return _((u"Email report to users with local role ${localrole} on "
                  u"the object"),
                 mapping=dict(localrole=self.localrole))

class MailActionExecutor(object):
    """The executor for this action.
    """
    implements(IExecutable)
    adapts(Interface, IMailLocalRoleAction, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        mailhost = getToolByName(aq_inner(self.context), "MailHost")

        if not mailhost:
            raise ComponentLookupError(
                'You must have a Mailhost utility to execute this action')

        source = self.element.source
        urltool = getToolByName(aq_inner(self.context), "portal_url")
        membertool = getToolByName(aq_inner(self.context), "portal_membership")

        portal = urltool.getPortalObject()
        email_charset = portal.getProperty('email_charset')
        if not source:
            # no source provided, looking for the site wide from email
            # address
            from_address = portal.getProperty('email_from_address')
            if not from_address:
                raise ValueError("You must provide a source address for this \
action or enter an email in the portal properties")
            from_name = portal.getProperty('email_from_name').strip('"')
            source = '"%s" <%s>' % (from_name, from_address)

        obj = self.event.object
        event_title = safe_unicode(obj.Title())
        event_url = obj.absolute_url()

        # search through all local roles on the object, and add
        # users's email to the recipients list if they have the local
        # role stored in the action
        local_roles = obj.get_local_roles()
        if len(local_roles) == 0:
            return True
        recipients = set()
        for user, roles in local_roles:
            rolelist = list(roles)
            if self.element.localrole in rolelist:
                recipients.add(user)

        # check for the acquired roles
        if self.element.acquired:
            sharing_page = obj.unrestrictedTraverse('@@sharing')
            acquired_roles = sharing_page._inherited_roles()
            acquired_users = [r[0] for r in acquired_roles
                              if self.element.localrole in r[1]]
            recipients.update(acquired_users)

        # check to see if the recipents are users or groups
        group_recipients = []
        new_recipients = []
        group_tool = portal.portal_groups
        
        def _getGroupMemberIds(group):
            """ Helper method to support groups in groups. """
            members = []
            for member_id in group.getGroupMemberIds():
                subgroup = group_tool.getGroupById(member_id)
                if subgroup is not None:
                    members.extend(_getGroupMemberIds(subgroup))
                else:
                    members.append(member_id)
            return members

        for recipient in recipients:
            group = group_tool.getGroupById(recipient)
            if group is not None:
                group_recipients.append(recipient)                
                [new_recipients.append(user_id)
                 for user_id in _getGroupMemberIds(group)]
        
        for recipient in group_recipients:
            recipients.remove(recipient)

        for recipient in new_recipients:
            recipients.add(recipient)

        # look up e-mail addresses for the found users
        recipients_mail = set()
        for user in recipients:
            recipient_prop = membertool.getMemberById(
                user).getProperty('email')
            if recipient_prop != None and len(recipient_prop) > 0:
                recipients_mail.add(recipient_prop)

        message = self.element.message.replace("${url}", event_url)
        message = message.replace("${title}", event_title)

        subject = self.element.subject.replace("${url}", event_url)
        subject = subject.replace("${title}", event_title)

        for recipient in recipients_mail:
            mailhost.secureSend(message.encode(email_charset), recipient, source,
                                subject=subject, subtype='plain',
                                charset=email_charset, debug=False)
        return True


class MailLocalRoleAddForm(AddForm):
    """
    An add form for the mail action
    """
    form_fields = form.FormFields(IMailLocalRoleAction)
    label = _plone(u"Add Mail Action")
    description = _plone(u"A mail action that can mail plone users who have "
                         u"a local role on the object")
    form_name = _plone(u"Configure element")

    def create(self, data):
        a = MailLocalRoleAction()
        form.applyChanges(a, self.form_fields, data)
        return a


class MailLocalRoleEditForm(EditForm):
    """
    An edit form for the mail action
    """
    form_fields = form.FormFields(IMailLocalRoleAction)
    label = _plone(u"Edit Mail Local Role Action")
    description = _plone(u"A mail action that can mail plone users who have "
                         u"a local role on the object")
    form_name = _plone(u"Configure element")
