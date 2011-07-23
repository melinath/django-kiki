from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from kiki.mail import route_email
from kiki.models import UserEmail, MailingList, sync_user_emails
from cStringIO import StringIO


class MailingListTest(TestCase):
	def setUp(self):
		self.user1 = User(username="username")
		self.user1.set_password("password")
		self.user1.save()
		self.user2 = User(username="test")
		self.user1.set_password("test")
		self.user1.save()
		self.useremail = UserEmail.objects.create(email='mrow@test.com')
		self.site = Site.objects.create(name="Hello", domain="test.com")
		self.mailing_list = MailingList.objects.create(name="Test List", address="test-list", site=self.site)
	
	def test_email_sync(self):
		user = self.user1
		user.email = "email@test.com"
		user.save()
		try:
			useremail = user.emails.get(email='email@test.com')
		except UserEmail.DoesNotExist:
			self.fail("Email did not sync!")
	
	def test_subscription(self):
		user = self.user1
		user.email = "email@test.com"
		user.save()
		useremail = self.useremail
		unused_email = "unused@test.com"
		mailing_list = self.mailing_list
		
		mailing_list.subscribe(user.email)
		mailing_list.subscribe(useremail.email)
		mailing_list.subscribe(unused_email)
		self.assertTrue(user in mailing_list.subscribed_users.all())
		self.assertTrue(useremail in mailing_list.subscribed_emails.all())
		self.assertTrue(mailing_list.is_subscribed(user.email))
		self.assertTrue(mailing_list.is_subscribed(useremail.email))
		self.assertTrue(mailing_list.is_subscribed(unused_email))
		
		mailing_list.unsubscribe(user.email)
		mailing_list.unsubscribe(useremail.email)
		mailing_list.unsubscribe(unused_email)
		self.assertFalse(user in mailing_list.subscribed_users.all())
		self.assertFalse(useremail in mailing_list.subscribed_emails.all())
		self.assertFalse(mailing_list.is_subscribed(user.email))
		self.assertFalse(mailing_list.is_subscribed(useremail.email))
		self.assertFalse(mailing_list.is_subscribed(unused_email))
	
	def create_test_email(self, from_email, to, subject='hello', body='This is clearly a test.'):
		mail.outbox = []
		mail.send_mail(subject, body, from_email, to)
		msg = StringIO(str(mail.outbox[0].message()))
		mail.outbox = []
		return msg
	
	def test_email_subscription(self):
		"Tests that an unknown email sent to <list>-subscribe@<domain> will be created and subscribed correctly."
		address = "emailed-in@test.com"
		mailing_list = self.mailing_list
		email = self.create_test_email(address, ["%s-subscribe@%s" % (mailing_list.address, mailing_list.site.domain)])
		route_email(email)
		import pdb
		pdb.set_trace()
		self.assertEquals(len(mail.outbox), 1)
		self.assertTrue(mailing_list.is_subscribed(address))
		email = self.create_test_email(address, ["%s-unsubscribe@%s" % (mailing_list.address, mailing_list.site.domain)])
		route_email(email)
		self.assertEquals(len(mail.outbox), 1)
		self.assertFalse(mailing_list.is_subscribed(address))