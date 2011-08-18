from email.utils import getaddresses

from django.core.mail.message import make_msgid, EmailMessage
from django.utils.translation import ugettext_lazy as _

from kiki.message import KikiMessage


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
	"""Given a python :class:`email.Message` object, return a corresponding class:`kiki.message.KikiMessage` object."""
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
	return KikiMessage(**kwargs)


def set_list_headers(msg, list_):
	"""
	Modifies the headers of a django.core.mail.EmailMessage in-place for a specific list.
	
	"""
	reply_to = msg.extra_headers.get('reply-to', None)
	msg.extra_headers.update({
		'X-Been-There': list_.address,
		'Reply-To': ', '.join(() if reply_to is None else (reply_to,) + (list_.address,)),
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

def create_test_email(from_email, to, subject='hello', body='This is clearly a test.', headers=None):
	"""
	Returns a string representation of an email message.
	
	"""
	headers = headers or {}
	msg = EmailMessage(subject, body, from_email, to, headers=headers)
	msg_str = msg.message().as_string()
	return msg_str
