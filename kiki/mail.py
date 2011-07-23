from django.core.mail.utils import DNS_NAME
from django.db.models import Q
from sys import stdin
import email
from email.parser import Parser
import smtplib
from django.conf import settings
from kiki.message import SteppingOutMessage
from kiki.notifications import delivery_failure, permissions_failure
from cStringIO import StringIO


MAX_SMTP_RECIPS = 99 # see http://people.dsv.su.se/~jpalme/ietf/mailing-list-behaviour.txt


def route_email(input):
	"""
	Steps:
		1. parse the input
		2. get all the mailing lists the message is sent to.
		3. for each mailing list, send the message through to all users.
			(but of course only if the sender has permission.)
	
	New Step List:
		1. Receive message.
		2. parse to+cc fields
		   -- save the data as metadata somewhere on the message.
		3. check if there are any mailing lists matching to or cc addresses.
		   -- if not, bounce the message. raise an error?
		4. check if the sender matches one of the allowed posters.
		   -- if not, bounce the message.
		5. add the list headers - should have a custom function.
		6. forward the message.
	"""
	msg = parse_email(input)
	try:
		msg.parse_addrs()
		if msg.missing_addresses:
			delivery_failure(msg, msg.missing_addresses)
		
		if msg.commands:
			for command in msg.commands:
				command(email=msg.original_sender)
		
		if not msg.mailing_lists:
			# Then stop here
			if msg.missing_addresses:
				msg.log.error("Delivery Error: All addresses failed (or were commands)")
			return
		
		# From here on, we know the mailing lists in question. The question is: who
		# is sending the message, and which mailing lists do they have permission to
		# send to? So: 1. What is the sending address? Could be envelope sender,
		# sender, from...
		
		# Does the user have permission to post to each mailing list? If not, note.
		rejected = set()
		
		for mailing_list in msg.mailing_lists.copy():
			if not mailing_list.can_post(msg.original_sender):
				rejected.add(mailing_list.full_address)
				msg.mailing_lists.remove(mailing_list)
		
		if rejected:
			permissions_failure(msg, rejected)
		
		if not msg.mailing_lists:
			return
		
		recipients = get_recipients(msg.mailing_lists, exclude=msg.skip_addresses)
		msg.cook_headers()
		forward(msg, recipients)
	except:
		msg.log.exception('')


def parse_email(input):
	"""
	Given an input, parses it as a python Message object, Forget EmailMessage -
	just turns it back to a Message in the end anyway.
	"""
	input.seek(0)
	msg = Parser(SteppingOutMessage).parse(input)
	msg.log.info("Received message: %s" % msg)
	return msg


def add_recipient_emails(qs, recipient_set):
	for item in qs:
		if item.email:
			recipient_set.add(item.email)


def get_recipients(mailing_lists, exclude):
	recipients = set()
	for mailing_list in mailing_lists:
		add_recipient_emails(mailing_list.subscribed_emails.exclude(email__in=exclude), recipients)
		add_recipient_emails(mailing_list.subscribed_users.exclude(email__in=exclude), recipients)
		
		for group in mailing_list.subscribed_groups.all():
			add_recipient_emails(group.users.exclude(email__in=exclude), recipients)
		
		for position in mailing_list.subscribed_officer_positions.all():
			add_recipient_emails(position.users.exclude(email__in=exclude), recipients)
		
		add_recipient_emails(mailing_list.moderator_emails.exclude(email__in=exclude), recipients)
		add_recipient_emails(mailing_list.moderator_users.exclude(email__in=exclude), recipients)
		
		for group in mailing_list.moderator_groups.all():
			add_recipient_emails(group.users.exclude(email__in=exclude), recipients)
		
		for position in mailing_list.moderator_officer_positions.all():
			add_recipient_emails(position.users.exclude(email__in=exclude), recipients)
	return recipients


def forward(msg, recips):
	connection = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, local_hostname=DNS_NAME.get_fqdn())
	
	text = msg.as_string()
	
	# Really, this should be sent separately to each list so that the bounce is
	# correct, but for now, just pick a random list.
	env_sender_list = msg.mailing_lists.pop()
	env_sender = env_sender_list.address + '-bounce@' + env_sender_list.site.domain

	while len(recips) > MAX_SMTP_RECIPS:
		chunk = set(list(recips)[0:MAX_SMTP_RECIPS])
		connection.sendmail(env_sender, chunk, text)
		recips -= chunk

	refused = connection.sendmail(env_sender, recips, text)
	connection.quit()
	if refused:
		# should I send this back to the sender, as well?
		msg.log.error("Message delivery failed at %s" % ', '.join(refused.keys()))
	msg.log.info("Forwarded message")