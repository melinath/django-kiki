from email.utils import get_addresses

from django.core.mail.message import EmailMessage, make_msgid


def message_to_django(msg):
	"""Given a python :class:`email.Message` object, return a corresponding class:`django.core.mail.EmailMessage` object."""
	payload = msg.get_payload()
	if msg.is_multipart():
		# TODO: is this the correct way to determine "body" vs "attachments"?
		body = payload[0]
		attachments = payload[1:]
	else:
		body = payload
		attachments = None
	
	# For now, let later header values override earlier ones. TODO: This should be more complex.
	headers = dict([(k.lower(), v) for k, v in msg.items()])
	
	if 'message-id' not in headers:
		headers['message-id'] = make_msgid()
	
	to = [addr[1] for addr in get_addresses(headers.pop('to', ''))]
	cc = [addr[1] for addr in get_addresses(headers.pop('cc', ''))]
	bcc = [addr[1] for addr in get_addresses(headers.pop('bcc', ''))]
	
	kwargs = {
		'subject': headers.pop('subject', ''),
		'body': body,
		'from_email': headers.pop('From', ''),
		'to': to,
		'bcc': bcc,
		'attachments': attachments,
		'headers': headers,
		'cc': cc
	}
	return EmailMessage(**kwargs)
