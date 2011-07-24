from datetime import datetime
from email import message_from_string
import smtplib
from socket import error as socket_error

from celery.decorators import task
from django.core.mail import get_connection
from django.db.models import Q

from kiki.models import Message, ListMessage
from kiki.utils import message_to_django, sanitize_headers, set_list_headers, set_user_headers

@task
def receive_email(msg_str):
	"""
	Given a string representation of an email message, parse it into a Django EmailMessage. Once this succeeds, the result should be stored in the database and added to the queue for further processing.
	
	"""
	received = datetime.now()
	python_msg = message_from_string(msg_str)
	sanitize_headers(python_msg)
	msg = message_to_django(python_msg)
	msg_id = msg.extra_headers['message-id']
	
	# If the msg_id already exists in the database, then ignore this message.
	try:
		Message.objects.get(message_id=msg_id)
	except Message.DoesNotExist:
		message = Message(message_id=msg_id, received=received, original_message=msg_str, from_email=msg.from_email)
		message.set_processed(msg)
		message.save()


@task
def attach_message_to_lists(msg_id):
	"""
	Attaches the message with the given id to the appropriate email lists.
	
	"""
	try:
		msg = Message.objects.get(pk=msg_id, status__in=[Message.RECEIVED, Message.COMMANDS])
	except Message.DoesNotExist:
		return
	
	if msg.status == msg.RECEIVED:
		msg.status = msg.ATTACHED
	else:
		msg.status = msg.ATT_COMM
	msg.save()
	
	recipients = msg.get_processed().recipients()
	if not recipients:
		return
	
	lists = MailingList.objects.for_addresses(recipients)
	
	for list_ in lists:
		list_msg = ListMessage.objects.create(message=msg, mailing_list=list_, processed_message=msg.processed_message)


@task
def create_message_commands(msg_id):
	"""
	Create the commands represented by the message with the given id.
	
	"""
	pass


@task
def check_command_perms(cmd_id):
	"""
	Checks whether the message has the required permissions to execute the given command.
	
	"""
	pass


@task
def run_command(cmd_id):
	"""
	Runs the given command.
	
	"""
	pass


@task
def check_list_message_perms(list_msg_id):
	"""
	Checks whether the message sent to a particular list has the required permissions and marks it either as ``Accepted``, ``Rejected``, or ``Requires Moderation``.
	
	"""
	try:
		list_msg = ListMessage.objects.select_related(depth=1).get(pk=list_msg_id, status=ListMessage.UNPROCESSED)
	except ListMessage.DoesNotExist:
		return
	
	msg = list_msg.get_processed()
	
	if list_msg.mailing_list.can_post(msg.from_email):
		list_msg.status = ListMessage.ACCEPTED
	elif list_msg.mailing_list.moderation_enabled:
		list_msg.status = ListMessage.REQUIRES_MODERATION
	else:
		list_msg.status = ListMessage.REJECTED
	
	list_msg.save()


@task
def prep_list_message(list_msg_id):
	"""
	Prepares the message to be sent to a particular list by setting the headers and performing any other final processing.
	
	"""
	try:
		list_msg = ListMessage.objects.select_related('mailing_list').get(pk=list_msg_id, status=ListMessage.ACCEPTED)
	except ListMessage.DoesNotExist:
		return
	
	list_msg.status = ListMessage.PREPPED
	list_msg.save()
	
	msg = list_msg.get_processed()
	set_list_headers(msg, list_msg.mailing_list)
	list_msg.set_processed(msg)


@task
def send_list_message(list_msg_id):
	"""
	Sends the message to its list.
	
	"""
	try:
		list_msg = ListMessage.objects.select_related('mailing_list').get(pk=list_msg_id, status=ListMessage.PREPPED)
	except ListMessage.DoesNotExist:
		return
	
	list_msg.status = ListMessage.SENT
	list_msg.save()
	
	msg = list_msg.get_processed()
	recipients = list_msg.mailing_list.get_recipients().only('email')
	
	connection = None
	failed = []
	
	for user in recipients:
		set_user_headers(msg, user)
		# Try/catch similar to django-mailer.
		try:
			if connection is None:
				connection = msg.get_connection()
			msg.connection = connection
			msg._recipients = [user.email]
			msg.send()
		except (socket_error, smtplib.SMTPSenderRefused, smtplib.SMTPRecipientsRefused, smtplib.SMTPAuthenticationError):
			failed.append(user)
			# reset the connection.
			connection = None
