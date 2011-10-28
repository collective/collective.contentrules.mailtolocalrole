Introduction
============

Using content rules in Plone 3 it's very easy to register for certain events
and perform actions upon occurrence. One of these actions provided by Plone 3
is a mail action. 

A limitation in the supplied mail action is that one can only provide fixed
email addresses. But sometimes you'd like to send an email to a user having a
certain role on the object that was involved in triggering the content rule.

An examplary use case and reason for creation of this package is the reviewer 
role. If an object in a certain location of the site is submitted for
publication, you would like to inform the user that has the 'reviewer' role
on this area of the site that a new document/object is available for review.

Before contentrules was available in Plone 3 the place to add this functionality
was to to create a python script and attach it to the workflow 'submit' 
transition that was used for the objects.

.. Note::
   This product will be superceded by `collective.contentrules.mailtorole`, 
   which can send mail to all members having a role on the object, including 
   global roles.

Installation
============

Add collective.contentrules.mailtolocalrole to your buildout as an egg or
from source. No (generic setup) installation is necessary.

    Versions before 1.2 did not use the z3c.autoinclude plugin, so you would
    need to add the package to the zcml slug list of your [instance] section.

Usage
=====

Go to the Plone Control Panel, select Content Rules and add a new Rule. 
Under 'actions' you now have a new option: Send email to users with local role.

Stability / feedback
====================

this stand alone package has been derived from an implentation done during
a customer project. It's in production use, there are some tests, but it's
not 1.0 yet. Feedback is appreciated.

0.7 update: Several users have commented and sent feedback/patches. Thank you!


Caveat
======

This contentrule only works on **local** roles. If you check for the review role
and you have a user a or a group in your user settings defined as a reviewer
as a global role, these will *NOT* be picked up. 

Also, if you assign users a global review role, you cannot assign them a 
local role anymore because the Sharing tab will show an inherited sign
instead of a checkbox.

Worse: if you first assign a user/group a local role and
afterwards also give him a global role in the user settings in the Plone
Control Panel, the local role will be hidden in the sharing tab of the content
you've set the local role to, but will still be active in the background. The
sharing tab won't even show you the global role unless you explicitly search
for the user (which is logical, otherwise every sharing tab woul be spammed
with global roles). But when you remove the global role the local role will
show up again.


This package was first designed for a use case with local roles, I hadn't
really thought of checking for global roles as well. We could add this feature
in a future version if there is demand for it, but we would have to change the
package name, collective.contentrules.mailtorole... ;-)

Credits
=======

Most of this package has been directly copied from the plone.app.contentrules
mail action. Additions have been made to check for directly assigned local
roles, acquired roles, fetching the e-mail To addresses from the user objects,
modification of the control panel action, translations and tests.
 
