from django.core.exceptions import ValidationError
from django.core.mail import get_connection
from django.template.defaultfilters import capfirst
from email.utils import formatdate, make_msgid, getaddresses
from smtplib import SMTPException
from kiki.commands import add_list_command_headers


COMMASPACE = ', '

# Supposedly, sending to > 49 people at once results in spam flags flying.
# If this turns out not to be the case, this should be 99. See
# http://people.dsv.su.se/~jpalme/ietf/mailing-list-behaviour.txt
MAX_SMTP_RECIPS = 49


def add_emails_to_list(mailing_list, emails):
	errors = []
	for email in emails:
		try:
			mailing_list.subscribe(email)
		except ValidationError, e:
			errors.append(e)
			continue
	
	return errors


def precook_headers(msg):
	"""
	Set and modify headers on a message that need to be there or need to be
	gone, no matter which list the message ends up going to. This will be
	performed on inbound messages.
	"""
	if 'message-id' not in msg:
		msg['Message-ID'] = make_msgid()
	if 'date' not in msg:
		msg['Date'] = formatdate()
	del msg['domainkey-signature']
	del msg['dkim-signature']
	del msg['authentication-results']
	
	# Remove various headers a la Mailman's cleansing.
	del msg['approved']
	del msg['approve']
	del msg['urgent']
	del msg['return-receipt-to']
	del msg['disposition-notification-to']
	del msg['x-confirm-reading-to']
	del msg['x-pmrqc']
	del msg['archived-at']


def cook_headers(msg, mailing_list):
	"""
	Cook the headers specific to a mailing list.
	See:
	- http://www.jamesshuggins.com/h/web1/list-email-headers.htm
	- http://www.faqs.org/rfcs/rfc2076.html
	"""
	add_list_command_headers(msg, mailing_list)
	del msg['list-id']
	msg['List-ID'] = mailing_list.list_id_header
	
	msg['X-BeenThere'] = mailing_list.address
	
	if 'precedence' not in msg:
		msg['Precedence'] = 'list'
	
	# Preserve reply-to, but smoosh them together since only one reply-to header
	# is allowed.
	reply_to = set([address.lower() for real_name, address in getaddresses(msg.get_all('reply-to', []))])
	reply_to.add(mailing_list.address)
	del msg['reply-to']
	if reply_to:
		msg['Reply-To'] = COMMASPACE.join(reply_to)
	
	# add a subject prefix for this list.
	if mailing_list.subject_prefix:
		subject = msg.get('subject', '(no subject)'))
		del msg['subject']
		msg['subject'] = "[%s] %s" % (mailing_list.subject_prefix, subject)


def postcook_headers(msg, mailing_list, recipient_email):
	"Directly before sending, add headers on a user-by-user basis."
	del msg['x-recipient']
	del msg['x-subscriber']
	msg['X-Recipient'] = msg['X-Subscriber'] = "<%s>" % recipient_email


def send_mail(msg, mailing_list, recipients, connection=None):
	if connection is None:
		connection = get_connection()
	
	envelope_sender = get_command('bounce').get_address(mailing_list)
	
	for i in range(0,len(recipients), MAX_SMTP_RECIPS):
		chunk = recipients[i:i+MAX_SMTP_RECIPS]
		django_send_mail(msg['subject'], msg.as_string(), envelope_sender, chunk, connection)
	
	# Django's EmailMessage class doesn't let me set just the envelope sender...
	# Python's Message class can't interface with django email backends.
	# Customization time?