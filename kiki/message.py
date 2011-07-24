from django.utils.encoding import force_unicode
from django.core.mail import EmailMessage

class KikiMessage(EmailMessage):
	"""
	This is similar to a django EmailMessage, but overrides recipients() to return arbitrary recipients rather than a concatenation of the to, cc, and bcc attributes.
	
	"""
	_recipients = None
	
	def recipients(self):
		return self._recipients or []