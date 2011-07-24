import time

from celery import task, registry
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail

from kiki.models import ListMessage
from kiki.tasks import receive_email


class RoutingTest(TestCase):
	fixtures = ['routing_test.json']
	
	def setUp(self):
		self.original_email = self.create_test_email("unused@unused.com", ["hello-world@example.com"])
	
	def create_test_email(self, from_email, to, subject='hello', body='This is clearly a test.', headers=None):
		headers = headers or {}
		mail.outbox = []
		mail.EmailMessage(subject, body, from_email, to, headers=headers).send()
		msg = str(mail.outbox[0].message())
		mail.outbox = []
		return msg
	
	def test_routing(self):
		mail.outbox = []
		receive_email.apply(args=(self.original_email,))
		list_messages = ListMessage.objects.all()
		while not list_messages:
			time.sleep(5)
			list_messages = ListMessage.objects.all()
		
		self.assertEqual(len(mail.outbox), len(list_messages))