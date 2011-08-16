import time
from email import message_from_string

from celery import task, registry
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail

from kiki.models import ListMessage
from kiki.tasks import receive_email
from kiki.utils import create_test_email, message_to_django


class RoutingTest(TestCase):
	fixtures = ['routing_test.json']
	
	def setUp(self):
		self.original_email = create_test_email("unused@unused.com", ["hello-world@example.com"])
	
	def test_routing(self):
		mail.outbox = []
		receive_email.apply(args=(self.original_email,))
		time.sleep(1)
		list_messages = ListMessage.objects.all()
		
		self.assertEqual(len(mail.outbox), len(list_messages))


class EmailParsingTest(TestCase):
	def setUp(self):
		self.from_email = "unused@unused.com"
		self.to = ["hello-world@example.com"]
		msg_str = create_test_email(self.from_email, self.to)
		python_msg = message_from_string(msg_str)
		self.msg = message_to_django(python_msg)
	
	def test_message_to_django_from(self):
		self.assertEqual(self.msg.from_email, self.from_email)
	
	def test_message_to_django_to(self):
		self.assertEqual(self.msg.to, self.to)