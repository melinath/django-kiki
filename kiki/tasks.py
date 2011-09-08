from celery.decorators import task
from django.contrib.auth.models import User

from kiki.models import MailingList, Message, ListMessage, ListCommand
from kiki.utils.routing import receive_email, create_message_commands, list_post, prep_list_message, send_list_message


COMMAND_TASKS = {}


@task(ignore_result=True)
def receive_email_task(msg_str):
	"""
	Runs :func:`kiki.utils.routing.receive_email` and, if a message was created, passes that message on to the :func:`create_message_commands_task`.
	
	"""
	message, created = receive_email(msg_str)
	if created:
		create_message_commands_task.delay(message.pk)


@task(ignore_result=True)
def create_message_commands_task(msg_id):
	"""
	Runs :func:`kiki.utils.routing.create_message_commands` and immediately passes the resulting :class:`kiki.models.ListCommand`\ s on to the appropriate tasks.
	
	"""
	try:
		msg = Message.objects.get(pk=msg_id, status__in=[Message.UNPROCESSED, Message.FAILED])
	except Message.DoesNotExist:
		return
	
	list_cmds = create_message_commands(msg)
	for list_cmd in list_cmds:
		COMMAND_TASKS[list_cmd.command].delay(list_cmd.pk)


@task(ignore_result=False)
def list_post_task(list_cmd_id):
	"""
	Runs :func:`kiki.utils.routing.list_post` and immediately passes the resulting list message on to the next processing step.
	
	"""
	try:
		list_cmd = ListCommand.objects.select_related().get(pk=list_cmd_id, status=ListCommand.UNPROCESSED, command="post")
	except ListCommand.DoesNotExist:
		return
	
	list_msg = list_post(list_cmd)
	
	if list_msg and list_msg.status == ListMessage.ACCEPTED:
		prep_list_message_task.delay(list_msg.pk)
COMMAND_TASKS['post'] = list_post_task


@task(ignore_result=True)
def prep_list_message_task(list_msg_id):
	"""
	Runs :func:`kiki.utils.routing.prep_list_message` on the :class:`.ListMessage` and immediately passes the list message on to the next processing step.
	
	"""
	try:
		list_msg = ListMessage.objects.select_related('mailing_list').get(pk=list_msg_id, status=ListMessage.ACCEPTED)
	except ListMessage.DoesNotExist:
		return
	
	prep_list_message(list_msg)
	collect_list_message_recipients.delay(list_msg_id)


@task(ignore_result=True)
def collect_list_message_recipients(list_msg_id):
	"""
	Collects the recipients for a :class:`kiki.models.ListMessage` and spawns tasks to email each recipient.
	
	"""
	try:
		list_msg = ListMessage.objects.select_related('mailing_list').get(pk=list_msg_id, status=ListMessage.PREPPED)
	except ListMessage.DoesNotExist:
		return
	
	list_msg.status = ListMessage.SENT
	list_msg.save()
	
	recipient_pks = list_msg.mailing_list.get_recipients().values_list('pk', flat=True)
	for recipient_pk in recipient_pks:
		send_list_message_task.delay(list_msg_id, recipient_pk)


@task(ignore_result=True)
def send_list_message_task(list_msg_id, user_pk):
	"""
	Asynchronously sends the message to a single user.
	
	"""
	try:
		list_msg = ListMessage.objects.only('processed_message').get(pk=list_msg_id, status=ListMessage.SENT)
		user = User.objects.only('email').get(pk=user_pk)
	except (ListMessage.DoesNotExist, User.DoesNotExist):
		return
	send_list_message(list_msg, user)
