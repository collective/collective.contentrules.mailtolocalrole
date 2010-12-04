# -*- coding: utf-8 -*-

from email.MIMEText import MIMEText
from zope.component import getUtility, getMultiAdapter, getSiteManager
from zope.component.interfaces import IObjectEvent
from zope.interface import implements

from plone.app.contentrules.rule import Rule
from plone.app.contentrules.tests.base import ContentRulesTestCase
from collective.contentrules.mailtolocalrole.actions.mail import (
    MailLocalRoleAction, MailLocalRoleEditForm, MailLocalRoleAddForm)
from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.rule.interfaces import IRuleAction, IExecutable

from Products.MailHost.interfaces import IMailHost
from Products.SecureMailHost.SecureMailHost import SecureMailHost

from Products.PloneTestCase.setup import default_user

from Products.CMFCore.utils import getToolByName

# basic test structure copied from plone.app.contentrules test_action_mail.py


class DummyEvent(object):
    implements(IObjectEvent)

    def __init__(self, object):
        self.object = object


class DummySecureMailHost(SecureMailHost):
    meta_type = 'Dummy secure Mail Host'

    def __init__(self, id):
        self.id = id
        self.sent = []

    def _send(self, mfrom, mto, messageText, debug=False):
        self.sent.append(messageText)


class TestMailAction(ContentRulesTestCase):

    def afterSetUp(self):
        self.setRoles(('Manager',))
        self.portal.invokeFactory('Folder', 'target')
        self.folder.invokeFactory('Document', 'd1',
            title=unicode('Wälkommen', 'utf-8'))
        # set the email address of the default_user.
        member = self.portal.portal_membership.getMemberById(default_user)
        member.setMemberProperties(dict(email="getme@frommember.com"))
        member = self.portal.portal_membership.getMemberById('portal_owner')
        member.setMemberProperties(dict(email="portal@owner.com"))

        # set up a group
        membership = getToolByName(self.portal, 'portal_membership')
        membership.addMember(
            'member1',
            'secret',
            ('Member',),
            (),
            properties={'email': 'somedude@url.com'})
        membership.addMember(
            'member2',
            'secret',
            ('Member',),
            (),
            properties={'email': 'anotherdude@url.com'})
        membership.addMember('member3', 'secret', ('Member', ), ())
        groups = getToolByName(self.portal, 'portal_groups')
        groups.addGroup('group1')
        groups.addPrincipalToGroup('member2', 'group1')
        self.folder.manage_setLocalRoles('member1', ['Reader', ])
        self.folder.manage_setLocalRoles('group1', ['Reader', ])

        # empty email address
        membership.addMember(
            'membernomail',
            'secret',
            ('Member',),
            (),
            properties={'email': ''})
        self.folder.invokeFactory('Document', 'd2',
            title=unicode('Wälkommen också', 'utf-8'))
        self.folder.d2.manage_setLocalRoles('membernomail', ['Reviewer', ])

    def testRegistered(self):
        element = getUtility(IRuleAction, name='plone.actions.MailLocalRole')
        self.assertEquals('plone.actions.MailLocalRole', element.addview)
        self.assertEquals('edit', element.editview)
        self.assertEquals(None, element.for_)
        self.assertEquals(IObjectEvent, element.event)

    def testInvokeAddView(self):
        element = getUtility(IRuleAction, name='plone.actions.MailLocalRole')
        storage = getUtility(IRuleStorage)
        storage[u'foo'] = Rule()
        rule = self.portal.restrictedTraverse('++rule++foo')

        adding = getMultiAdapter((rule, self.portal.REQUEST), name='+action')
        addview = getMultiAdapter((adding, self.portal.REQUEST),
                                  name=element.addview)
        self.failUnless(isinstance(addview, MailLocalRoleAddForm))

        addview.createAndAdd(data={'subject': 'My Subject',
                                   'source': 'foo@bar.be',
                                   'localrole': 'Owner',
                                   'acquired': True,
                                   'message': 'Hey, Oh!'})

        e = rule.actions[0]
        self.failUnless(isinstance(e, MailLocalRoleAction))
        self.assertEquals('My Subject', e.subject)
        self.assertEquals('foo@bar.be', e.source)
        self.assertEquals('Owner', e.localrole)
        self.assertEquals(True, e.acquired)
        self.assertEquals('Hey, Oh!', e.message)

    def testInvokeEditView(self):
        element = getUtility(IRuleAction, name='plone.actions.MailLocalRole')
        e = MailLocalRoleAction()
        editview = getMultiAdapter((e, self.folder.REQUEST),
                                   name=element.editview)
        self.failUnless(isinstance(editview, MailLocalRoleEditForm))

    def testExecute(self):
        self.loginAsPortalOwner()
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IMailHost)
        dummyMailHost = DummySecureMailHost('dMailhost')
        sm.registerUtility(dummyMailHost, IMailHost)
        e = MailLocalRoleAction()
        e.source = "foo@bar.be"
        e.localrole = "Owner"
        e.acquired = False
        e.message = u"Päge '${title}' created in ${url} !"
        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)),
                             IExecutable)
        ex()
        self.failUnless(isinstance(dummyMailHost.sent[0], MIMEText))
        mailSent = dummyMailHost.sent[0]
        self.assertEqual('text/plain; charset="utf-8"',
                        mailSent.get('Content-Type'))

        self.assertEqual("getme@frommember.com", mailSent.get('To'))
        self.assertEqual("foo@bar.be", mailSent.get('From'))
        self.assertEqual("P\xc3\xa4ge 'W\xc3\xa4lkommen' created in \
http://nohost/plone/Members/test_user_1_/d1 !",
                         mailSent.get_payload(decode=True))

    def testExecuteWithGroup(self):
        self.loginAsPortalOwner()
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IMailHost)
        dummyMailHost = DummySecureMailHost('dMailhost')
        sm.registerUtility(dummyMailHost, IMailHost)
        e = MailLocalRoleAction()
        e.source = "foo@bar.be"
        e.localrole = "Reader"
        e.acquired = True
        e.message = u"P√§ge '${title}' created in ${url} !"
        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)),
                             IExecutable)
        ex()
        self.failUnless(isinstance(dummyMailHost.sent[0], MIMEText))
        self.assertEqual(len(dummyMailHost.sent), 2)
        mailSentTo = [mailSent.get('To') for mailSent in dummyMailHost.sent]
        assert("somedude@url.com" in mailSentTo)
        assert("anotherdude@url.com" in mailSentTo)

    def testExecuteNoEmptyMail(self):
        self.loginAsPortalOwner()
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IMailHost)
        dummyMailHost = DummySecureMailHost('dMailhost')
        sm.registerUtility(dummyMailHost, IMailHost)
        e = MailLocalRoleAction()
        e.source = "foo@bar.be"
        e.localrole = "Reviewer"
        e.acquired = False
        e.message = u"Päge '${title}' created in ${url} !"
        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d2)),
                             IExecutable)
        ex()
        self.assertEqual(len(dummyMailHost.sent), 0)

    def testExecuteAcquired(self):
        self.loginAsPortalOwner()
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IMailHost)
        dummyMailHost = DummySecureMailHost('dMailhost')
        sm.registerUtility(dummyMailHost, IMailHost)
        e = MailLocalRoleAction()
        e.source = "foo@bar.be"
        e.localrole = "Owner"
        e.acquired = True
        e.message = u"Päge '${title}' created in ${url} !"
        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)),
                             IExecutable)
        ex()
        self.failUnless(isinstance(dummyMailHost.sent[0], MIMEText))
        self.failUnless(isinstance(dummyMailHost.sent[1], MIMEText))

        for mailSent in dummyMailHost.sent:

            self.assertEqual('text/plain; charset="utf-8"',
                            mailSent.get('Content-Type'))

            self.failUnless(mailSent.get('To') in ("getme@frommember.com",
                                                   "portal@owner.com"))
            self.assertEqual("foo@bar.be", mailSent.get('From'))
            self.assertEqual("P\xc3\xa4ge 'W\xc3\xa4lkommen' created in http://nohost/plone/Members/test_user_1_/d1 !",
                             mailSent.get_payload(decode=True))

    def testExecuteNoSource(self):
        self.loginAsPortalOwner()
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IMailHost)
        dummyMailHost = DummySecureMailHost('dMailhost')
        sm.registerUtility(dummyMailHost, IMailHost)
        e = MailLocalRoleAction()
        e.localrole = "Owner"
        e.acquired = False
        e.message = 'Document created !'
        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)),
                             IExecutable)
        self.assertRaises(ValueError, ex)
        # if we provide a site mail address this won't fail anymore
        sm.manage_changeProperties({'email_from_address': 'manager@portal.be'})
        ex()
        self.failUnless(isinstance(dummyMailHost.sent[0], MIMEText))
        mailSent = dummyMailHost.sent[0]
        self.assertEqual('text/plain; charset="utf-8"',
                        mailSent.get('Content-Type'))
        self.assertEqual("getme@frommember.com", mailSent.get('To'))
        self.assertEqual("Site Administrator <manager@portal.be>",
                         mailSent.get('From'))
        self.assertEqual("Document created !",
                         mailSent.get_payload(decode=True))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMailAction))
    return suite
