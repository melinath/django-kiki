from email.utils import get_addresses

from django.core.mail.message import EmailMessage, make_msgid
from django.utils.translation import ugettext_lazy as _


NO_SUBJECT = _(u"(no subject)")


def sanitize_headers(msg):
	"""
	Set and modify headers on an email.Message that need to be there no matter which list the message ends up being delivered to. Also remove headers that need to *not* be there.
	
	"""
	if 'message-id' not in msg:
		msg['Message-ID'] = make_msgid()
	if 'date' not in msg:
		msg['Date'] = formatdate()
	if 'subject' not in msg:
		msg['Subject'] = NO_SUBJECT
	if 'precedence' not in msg:
		msg['Precedence'] = 'list'
	
	del msg['domainkey-signature']
	del msg['dkim-signature']
	del msg['authentication-results']
	del msg['list-id']
	del msg['x-recipient']
	del msg['x-subscriber']
	
	# Preserve reply-to, but smoosh them together since only one reply-to header
	# is allowed.
	reply_to = set([address.lower() for real_name, address in getaddresses(msg.get_all('reply-to', []))])
	del msg['reply-to']
	if reply_to:
		msg['Reply-To'] = ", ".join(reply_to)
	
	# Remove various headers a la Mailman's cleansing.
	del msg['approved']
	del msg['approve']
	del msg['urgent']
	del msg['return-receipt-to']
	del msg['disposition-notification-to']
	del msg['x-confirm-reading-to']
	del msg['x-pmrqc']
	del msg['archived-at']


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


def set_list_headers(msg, list_):
	"""
	Modifies the headers of a django.core.mail.EmailMessage in-place for a specific list.
	
	"""
	msg.extra_headers.update({
		'X-Been-There': list_.address,
		'Reply-To': ', '.join((msg.extra_headers['reply-to'], list_.address)),
		'List-Id': list_._list_id_header(),
		'List-Post': list_._command_header(),
		'List-Subscribe': list_._command_header('subscribe'),
		'List-Unsubscribe': list_._command_header('unsubscribe'),
		'List-Help': list_._command_header('help'),
		'List-Archive': list_._command_header('archive'),
		#'List-Owner': list_._command_header('owner'),
	})
	
	if list_.subject_prefix:
		msg.subject = "[%s] %s" % (list_.subject_prefix, msg.subject)


def set_user_headers(msg, user):
	"""
	Modifies the headers of a django.core.mail.EmailMessage in-place for a specific user.
	
	"""
	msg.extra_headers.update({
		'x-recipient': "<%s>" % user.email,
		'x-subscriber': "<%s>" % user.email
	})
