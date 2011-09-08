import time
from email import message_from_string

from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail

from kiki.message import KikiMessage
from kiki.models import ListMessage, Message, ListCommand
from kiki.tasks import receive_email_task, create_message_commands_task, list_post_task, send_list_message_task
from kiki.utils.message import create_test_email
from kiki.utils.routing import receive_email, create_message_commands, list_post, prep_list_message, send_list_message


class RoutingTest(TestCase):
	fixtures = ['test_data.json']
	
	def test_receive_email(self):
		message, created = receive_email(create_test_email("unused@unused.com", ["hello-world@example.com"]))
		self.assertTrue(created)
		self.assertIsInstance(message, Message)
	
	def test_create_message_commands(self):
		message = Message.objects.get(pk=3)
		list_cmds = create_message_commands(message)
		self.assertGreater(len(list_cmds), 0)
		self.assertIsInstance(list_cmds[0], ListCommand)
	
	def test_list_post(self):
		command = ListCommand.objects.get(pk=2)
		message = list_post(command)
		self.assertIsInstance(message, ListMessage)
	
	def test_send_list_message(self):
		user = User.objects.get()
		list_msg = ListMessage.objects.get(pk=1)
		mail.outbox = []
		send_list_message(list_msg, user)
		self.assertEqual(len(mail.outbox), 1)
	
	def test_receive_email_task(self):
		mail.outbox = []
		result = receive_email_task.delay(create_test_email("unused@unused.com", ["hello-world@example.com"]))
		result.get()
		self.assertEqual(len(mail.outbox), 1)
	
	def test_create_message_commands_task(self):
		mail.outbox = []
		result = create_message_commands_task.delay(3)
		time.sleep(1)
		self.assertEqual(len(mail.outbox), 1)
	
	def test_list_post_task(self):
		mail.outbox = []
		result = list_post_task.delay(2)
		time.sleep(1)
		self.assertEqual(len(mail.outbox), 1)
	
	def test_send_list_message_task(self):
		mail.outbox = []
		list_msg = ListMessage.objects.get(pk=1)
		prep_list_message(list_msg)
		result = send_list_message_task.delay(1, 1)
		time.sleep(1)
		self.assertEqual(len(mail.outbox), 1)


class EmailParsingTest(TestCase):
	def setUp(self):
		self.from_email = "unused@unused.com"
		self.to = ["hello-world@example.com"]
		msg_str = create_test_email(self.from_email, self.to)
		python_msg = message_from_string(msg_str)
		self.msg = KikiMessage.from_python_message(python_msg)
	
	def test_message_to_django_from(self):
		self.assertEqual(self.msg.from_email, self.from_email)
	
	def test_message_to_django_to(self):
		self.assertEqual(self.msg.to, self.to)