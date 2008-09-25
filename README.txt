Introduction
============

Most of this package has been copied from the plone.app.contentrules mail 
action.

Using content rules in Plone 3 it's very easy to register for certain events
and perform actions upon occurrence. One of these actions provided by Plone 3
is a mail action. 

A limitation in the default mail action is that one can only provide a fixed
email address. But sometimes you'd like to send an email to a user having a
certain role on the object that was involved in triggering the content rule.

An obvious use case and reason for creation of this package is the reviewer 
role. If an object in a certain location of the site is created, you would
like to inform the user that has the 'reviewer' role on this area of the site
that a new document/object is available for review.

Before contentrules was available you'd had to create a python script and
attach it to the workflow of the content types involved.
