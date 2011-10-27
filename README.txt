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

Installation
============

Add collective.contentrules.mailtolocalrole to your buildout as an egg or
from source. No (generic setup) installation is necessary.

    Versions before 1.2 did not use the z3c.autoinclude plugin, so you would
    need to add the package to the zcml slug list of your [instance] section.

Usage
=====

Go to the Plone Control Panel, select Content Rules and add a new Rule. 
Under 'actions' you now have a new option: Send email to users with role.

The checkboxes "Acquire roles" and "Global roles" are worth noting:

- If both are unchecked, mail will only be sent to members having a local role 
  on the object.

- Checking "Acquire roles" will also send mail to users that have acquired the
  specified role from a parent of the object, ie. from higher up in the site.

- Checking "Global roles" will also send mail to users that have the specified
  role globally, that is in the entire site.

Stability / feedback
====================

this stand alone package has been derived from an implentation done during
a customer project. It's in production use, there are some tests, but it's
not 1.0 yet. Feedback is appreciated.

0.7 update: Several users have commented and sent feedback/patches. Thank you!

Credits
=======

Most of this package has been directly copied from the plone.app.contentrules
mail action. Additions have been made to check for directly assigned local
roles, acquired roles, fetching the e-mail To addresses from the user objects,
modification of the control panel action, translations and tests.
 
