from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import simplejson as json
from stepping_out.mail.validators import EmailNameValidator
from email.utils import parseaddr


SUBSCRIPTION_CHOICES = (
	('mod', 'Moderators',),
	('sub', 'Subscribers',),
	('all', 'Anyone',),
)


class UserEmail(models.Model):
	email = models.EmailField(unique=True)
	user = models.ForeignKey(User, related_name='emails', blank=True, null=True)

	def delete(self):
		user = self.user
		super(UserEmail, self).delete()
		if user and user.email == self.email:
			try:
				user.email = user.emails.all()[0].email
			except KeyError:
				user.email = ''
			user.save()

	def save(self, *args, **kwargs):
		super(UserEmail, self).save(*args, **kwargs)

		# replace all references to this instance in mailing lists with its user.
		subscribed_mailinglists = self.subscribed_mailinglist_set.all()
		if self.user and subscribed_mailinglists:
			for mailing_list in subscribed_mailinglists:
				mailing_list.subscribed_users.add(self.user)
				mailing_list.subscribed_emails.remove(self)

	def __unicode__(self):
		return self.email

	class Meta:
		app_label = 'mail'


def sync_user_emails(instance, created, **kwargs):
	if not created:
		try:
			email = UserEmail.objects.get(email=instance.email)
		except UserEmail.DoesNotExist:
			email = UserEmail(email=instance.email)
		email.user = instance
		email.save()


models.signals.post_save.connect(sync_user_emails, sender=User)

def get_email(email):
	"Return an existing UserEmail instance or None."
	if isinstance(email, User):
		return email.emails.get(email=email.email)
	
	if isinstance(email, (str, unicode)):
		email = parseaddr(email)[1]
		validate_email(email)
		try:
			return UserEmail.objects.get(email=email)
		except UserEmail.DoesNotExist:
			pass

	if isinstance(email, UserEmail):
		return email

	return None


class MailingListManager(models.Manager):
	def by_domain(self):
		"""
		Returns a dictionary of MailingList objects by domain and address.
		"""
		mlists = self.all()
		by_domain = {}
		for mlist in mlists:
			if mlist.site.domain not in by_domain:
				by_domain[mlist.site.domain] = {}

			by_domain[mlist.site.domain][mlist.address] = mlist

		return by_domain


class MailingList(models.Model):
	"""
	This model contains all options for a mailing list, as well as some helpful
	methods for accessing subscribers, moderators, etc.
	"""
	# Really this whole address/site thing is ridiculous, but I don't have the
	# time just now to fix it.
	DEFAULT_SITE = None
	objects = MailingListManager()

	name = models.CharField(max_length=50)
	address = models.CharField(max_length=100, validators=[EmailNameValidator()])
	site = models.ForeignKey(Site, verbose_name="@", default=DEFAULT_SITE)
	help_text = models.TextField(verbose_name='description', blank=True)

	subscribed_users = models.ManyToManyField(
		User,
		related_name = 'subscribed_mailinglist_set',
		blank = True,
		null = True
	)
	subscribed_groups = models.ManyToManyField(
		Group,
		related_name = 'subscribed_mailinglist_set',
		blank = True,
		null = True
	)
	subscribed_emails = models.ManyToManyField(
		UserEmail,
		related_name = 'subscribed_mailinglist_set',
		blank = True,
		null = True
	)

	who_can_post = models.CharField(
		max_length = 3,
		choices = SUBSCRIPTION_CHOICES
	)
	self_subscribe_enabled = models.BooleanField(
		verbose_name = 'self-subscribe enabled'
	)

	moderator_users = models.ManyToManyField(
		User,
		related_name = 'moderated_mailinglist_set',
		blank = True,
		null = True
	)
	moderator_groups = models.ManyToManyField(
		Group,
		related_name='moderated_mailinglist_set',
		blank = True,
		null = True
	)
	moderator_emails = models.ManyToManyField(
		UserEmail,
		related_name = 'moderated_mailinglist_set',
		blank = True,
		null = True
	)

	def __unicode__(self):
		return self.name

	def subscribe(self, email):
		email = get_email(email) or UserEmail.objects.create(email=email)

		if self.is_subscribed(email):
			return

		if email.user is None:
			self.subscribed_emails.add(email)
		else:
			self.subscribed_users.add(email.user)

	def unsubscribe(self, email):
		email = get_email(email)

		if email is None:
			return

		self.subscribed_emails.remove(email)
		if email.user is not None:
			self.subscribed_users.remove(email.user)

	def is_subscribed(self, email):
		# Subscribed means explicitly subscribed - not subscribed as part of a
		# group or position.
		email = get_email(email)

		if email is None:
			return False

		if email in self.subscribed_emails.all():
			return True

		if self.subscribed_users.filter(emails=email):
			return True

		return False

	def is_in_subscribed(self, email):
		email = get_email(email)

		if email is None or email.user is None:
			return False

		if self.subscribed_groups.filter(users__emails=email):
			return True

		return False

	def is_moderator(self, email):
		# This means explicitly a moderator - not a moderator as part of a
		# group or position.
		email = get_email(email)

		if email is None:
			return False

		if email in self.moderator_emails.all():
			return True

		if self.moderator_users.filter(emails=email):
			return True

		return False

	def is_in_moderator(self, email):
		email = get_email(email)

		if email is None or email.user is None:
			return False

		if self.moderator_groups.filter(users__emails=email):
			return True

		return False

	def can_post(self, email):
		email = get_email(email)

		if self.who_can_post == 'all':
			return True

		if self.who_can_post == 'sub' and (self.is_subscribed(email) or self.is_in_subscribed(email)):
			return True

		if self.is_moderator(email) or self.is_in_moderator(email):
			return True

		return False

	@property
	def full_address(self):
		return '%s@%s' % (self.address, self.site.domain)

	class Meta:
		unique_together = ('site', 'address',)
		app_label = 'mail'