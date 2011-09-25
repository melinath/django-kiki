from email.utils import formatdate, getaddresses

from django.core.mail.message import make_msgid
from django.utils.translation import ugettext_lazy as _


NO_SUBJECT = _(u"(no subject)")


def sanitize_headers(msg):
	"""
	Set and modify headers on an :class:`email.Message` that need to be there no matter which list the message ends up being delivered to. Also remove headers that need to *not* be there.
	
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


def _build_command_header(mailing_list, command=None):
	"""Builds a command header for a mailing list and a given command."""
	if command:
		addr = "%s+%s@%s" % (mailing_list.local_part, command, mailing_list.domain.domain)
	else:
		addr = mailing_list.address
	return "<mailto:%s>" % addr


def set_list_headers(msg, list_):
	"""
	Modifies the headers of a django.core.mail.EmailMessage in-place for a specific list.
	
	"""
	reply_to = msg.extra_headers.get('reply-to', None)
	msg.extra_headers.update({
		'X-Been-There': list_.address,
		'Reply-To': ', '.join(() if reply_to is None else (reply_to,) + (list_.address,)),
		'List-Id': list_._list_id_header(),
		'List-Post': _build_command_header(list_),
		'List-Subscribe': _build_command_header(list_, 'subscribe'),
		'List-Unsubscribe': _build_command_header(list_, 'unsubscribe'),
		'List-Help': _build_command_header(list_, 'help'),
		# TODO: List-Archive should be a view.
		#'List-Archive': _build_command_header(list_, 'archive'),
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
