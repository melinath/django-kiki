from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase
from django.utils.http import int_to_base36

from kiki.models import MailingList, ListUserMetadata
from kiki.views import SubscriptionView, SubscriptionConfirmationView


class SubscriptionViewTestCase(TestCase):
	def setUp(self):
		self.view = SubscriptionView()
		self.user_email = 'hi@hi.com'
		self.site = Site.objects.get_current()
		self.site.name = "example.com"
		self.site.domain = "example.com"
		self.site.save()
		user = User.objects.create(username=self.user_email, email=self.user_email)
		mailing_list = MailingList.objects.create(name="Hello World", local_part="hello-world", domain=self.site)
		metadata = ListUserMetadata.objects.create(user=user, mailing_list=mailing_list)
		self.view.user = user
		self.view.mailing_list = mailing_list
		self.view.metadata = metadata
	
	def test_email_context(self):
		context = self.view.get_email_context()
		self.assertTrue(self.view.token_generator.check_token(self.view.metadata, context['token']))
		del context['token']
		expected_context = {
			'email': self.user_email,
			'mid': int_to_base36(self.view.metadata.pk),
			'metadata': self.view.metadata,
			'user': self.view.user,
			'mailing_list': self.view.mailing_list,
			'site_name': "example.com",
			'domain': "example.com",
			'protocol': 'http'
		}
		self.assertEqual(context, expected_context)
	
	def test_get_from_email(self):
		self.assertEqual(self.view.get_from_email(), "hello-world+bounce@example.com")
	
	def test_get_to_addresses(self):
		self.assertEqual(self.view.get_to_addresses(), [self.user_email])
