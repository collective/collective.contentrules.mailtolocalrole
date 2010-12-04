from zope.i18nmessageid import MessageFactory

mailtolocalroleMessageFactory = MessageFactory(
    'collective.contentrules.mailtolocalrole')


def initialize(context):
    """Intializer called when used as a Zope 2 product."""
