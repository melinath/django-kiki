from email.utils import getaddresses

from django.utils.encoding import force_unicode
from django.core.mail import EmailMessage


class KikiMessage(EmailMessage):
	"""
	This is similar to a django EmailMessage, but overrides recipients() to return arbitrary recipients rather than a concatenation of the to, cc, and bcc attributes.
	
	"""
	_recipients = None
	
	def recipients(self):
		return self._recipients or []
	
	@classmethod
	def from_python_message(cls, msg):
		"""Given a python :class:`email.Message` object, return a corresponding class:`kiki.message.KikiMessage` instance."""
		payload = msg.get_payload()
		if msg.is_multipart():
			# TODO: is this the correct way to determine "body" vs "attachments"?
			body = payload[0]
			attachments = payload[1:]
		else:
			body = payload
			attachments = None
		
		# For now, let later header values override earlier ones. TODO: This should be more complex.
		headers = dict([(k.lower(), v) for k, v in msg.items() if k not in ('to', 'cc', 'bcc')])
		
		to = [addr[1] for addr in getaddresses(msg.get_all('to', []))]
		cc = [addr[1] for addr in getaddresses(msg.get_all('cc', []))]
		bcc = [addr[1] for addr in getaddresses(msg.get_all('bcc', []))]
		
		kwargs = {
			'subject': headers.pop('subject', ''),
			'body': body,
			'from_email': headers.pop('from', ''),
			'to': to,
			'bcc': bcc,
			'attachments': attachments,
			'headers': headers,
			'cc': cc
		}
		return cls(**kwargs)