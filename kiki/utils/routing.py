from __future__ import with_statement

from datetime import datetime
from email import message_from_string

from django.db import transaction

from kiki.message import KikiMessage
from kiki.models import Message, MailingList, ListCommand, ListMessage
from kiki.utils.message import parse_command_address, set_list_headers, set_user_headers, sanitize_headers


def receive_email(msg_str):
	"""
	Given a string representation of an email message, parses it into a :class:`~kiki.message.KikiMessage`. Returns a (message, created) tuple, where ``created`` is False if the message was already in the database.
	
	"""
	received = datetime.now()
	python_msg = message_from_string(msg_str)
	sanitize_headers(python_msg)
	msg = KikiMessage.from_python_message(python_msg)
	msg_id = msg.extra_headers['message-id']
	
	# If the msg_id already exists in the database, then ignore this message.
	created = False
	try:
		message = Message.objects.get(message_id=msg_id)
	except Message.DoesNotExist:
		message = Message(message_id=msg_id, received=received, original_message=msg_str, from_email=msg.from_email)
		message.set_processed(msg)
		message.save()
		created = True
	return message, created


def create_message_commands(msg):
	"""
	Given a message, creates and returns a list of commands for that message and target mailing lists.
	
	"""
	if msg.status != Message.UNPROCESSED:
		return
	
	pmsg = msg.get_processed()
	recipients = pmsg.to + pmsg.cc + pmsg.bcc
	if not recipients:
		return
	
	# Make a map of commands to recipient lists.
	cmd_recips = {}
	
	for recipient in recipients:
		local, cmd, domain = parse_command_address(recipient)
		cmd_recips.setdefault(cmd, []).append('@'.join((local, domain)))
	
	try:
		with transaction.commit_on_success():
			for cmd in cmd_recips:
				lists = MailingList.objects.for_addresses(cmd_recips[cmd])
				list_cmds = [ListCommand.objects.create(message=msg, mailing_list=list_, command=cmd) for list_ in lists]
	except:
		msg.status = Message.FAILED
		msg.save()
		raise
	else:
		msg.status = Message.PROCESSED
		msg.save()
		return list_cmds


def list_post(list_cmd):
	"""
	Given a :class:`kiki.models.ListCommand` for a post, returns a :class:`kiki.models.ListMessage` based on that command, or ``None`` if the command was invalid. The :class:`kiki.models.ListMessage` will be marked either as "Accepted" or "Requires Moderation", and it will have the appropriate list headers set.
	
	"""
	if list_cmd.status != ListCommand.UNPROCESSED or list_cmd.command != "post":
		return None
	
	mailing_list = list_cmd.mailing_list
	can_post = mailing_list.can_post(list_cmd.message.from_email)
	moderation = mailing_list.moderation_enabled
	
	if not can_post and not moderation:
		# TODO: Email the user.
		list_cmd.status = ListCommand.REJECTED
		list_cmd.save()
		return None
	
	try:
		list_msg = ListMessage(message=list_cmd.message, mailing_list=mailing_list, status=ListMessage.ACCEPTED, processed_message=list_cmd.message.processed_message)
		if moderation and not can_post:
			list_msg.status = ListMessage.REQUIRES_MODERATION
		list_msg.save()
	except:
		list_cmd.status = ListCommand.FAILED
		list_cmd.save()
		raise
	else:
		
		list_cmd.status = ListCommand.PROCESSED
		list_cmd.save()
		return list_msg


def prep_list_message(list_msg):
	"""
	Runs :func:`kiki.utils.message.set_list_headers` on an accepted :class:`.ListMessage` and sets its status to :attr:`ListMessage.PREPPED`.
	
	"""
	if list_msg.status == ListMessage.ACCEPTED:
		msg = list_msg.get_processed()
		set_list_headers(msg, list_msg.mailing_list)
		list_msg.set_processed(msg)
		list_msg.status = ListMessage.PREPPED
		list_msg.save()
	return list_msg


def send_list_message(list_msg, user):
	"""
	Sends a copy of a :class:`kiki.models.ListMessage` to a single :class:`.User`.
	
	"""
	msg = list_msg.get_processed()
	set_user_headers(msg, user)
	msg._recipients = [user.email]
	msg.send()