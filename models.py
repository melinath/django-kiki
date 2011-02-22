from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import simplejson as json
from email.utils import parseaddr


class EmailAddress(models.Model):
	email = models.EmailField(unique=True)
	user = models.ForeignKey(User, related_name='emails', blank=True, null=True)

	#def delete(self):
	#	user = self.user
	#	super(EmailAddress, self).delete()
	#	if user and user.email == self.email:
	#		try:
	#			user.email = user.emails.all()[0].email
	#		except KeyError:
	#			user.email = ''
	#		user.save()
	#
	#def save(self, *args, **kwargs):
	#	super(EmailAddress, self).save(*args, **kwargs)
	#
	#	# replace all references to this instance in mailing lists with its user.
	#	subscribed_mailinglists = self.subscribed_mailinglist_set.all()
	#	if self.user and subscribed_mailinglists:
	#		for mailing_list in subscribed_mailinglists:
	#			mailing_list.subscribed_users.add(self.user)
	#			mailing_list.subscribed_emails.remove(self)
	
	def __unicode__(self):
		return self.email

	class Meta:
		app_label = 'mail'


#def sync_user_emails(instance, created, **kwargs):
#	if not created:
#		try:
#			email = EmailAddress.objects.get(email=instance.email)
#		except EmailAddress.DoesNotExist:
#			email = EmailAddress(email=instance.email)
#		email.user = instance
#		email.save()
#
#
#models.signals.post_save.connect(sync_user_emails, sender=User)


class MailingList(models.Model):
	"""
	This model contains all options for a mailing list, as well as some helpful
	methods for accessing subscribers, moderators, etc.
	"""
	MODERATORS = "mod"
	SUBSCRIBERS = "sub"
	ANYONE = "all"
	
	SUBSCRIPTION_CHOICES = (
		(MODERATORS, 'Moderators',),
		(SUBSCRIBERS, 'Subscribers',),
		(ANYONE, 'Anyone',),
	)
	
	name = models.CharField(max_length=50)
	address = models.EmailField()
	description = models.TextField(blank=True)
	
	who_can_post = models.CharField(max_length=3, choices=SUBSCRIPTION_CHOICES)
	self_subscribe_enabled = models.BooleanField(verbose_name = 'self-subscribe enabled')
	
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
		EmailAddress,
		related_name = 'subscribed_mailinglist_set',
		blank = True,
		null = True
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
		EmailAddress,
		related_name = 'moderated_mailinglist_set',
		blank = True,
		null = True
	)

	def __unicode__(self):
		return self.name

	def subscribe(self, obj):
		if isinstance(obj, EmailAddress):
			self.subscribed_emails.add(obj)
		elif isinstance(obj, User):
			self.subscribed_users.add(obj)
		elif isinstance(obj, Group):
			self.subscribed_groups.add(obj)
		else:
			raise TypeError(u"Invalid subscriber: %s" % unicode(obj))

	def unsubscribe(self, obj):
		if isinstance(obj, EmailAddress):
			self.subscribed_emails.remove(obj)
		elif isinstance(obj, User):
			self.subscribed_users.remove(obj)
		elif isinstance(obj, Group):
			self.subscribed_groups.remove(obj)
		else:
			raise TypeError(u"Invalid subscriber: %s" % unicode(obj))
	
	def is_subscriber(self, obj):
		if isinstance(obj, EmailAddress):
			return obj in self.subscribed_emails.all()
		elif isinstance(obj, User):
			return obj in self.subscribed_users.all()
		elif isinstance(obj, Group):
			return obj in self.subscribed_groups.all()
		else:
			raise TypeError(u"Invalid subscriber: %s" % unicode(obj))

	def is_implicit_subscriber(self, obj):
		if isinstance(obj, EmailAddress):
			return obj.user and (self.is_subscriber(obj.user) or self.is_implicit_subscriber(obj.user))
		elif isinstance(obj, User):
			return bool(self.subscribed_groups.filter(users=obj))
		elif isinstance(obj, Group):
			raise TypeError(u"Groups cannot be implicit subscribers.")
		else:
			raise TypeError(u"Invalid subscriber: %s" % unicode(obj))

	def is_moderator(self, email):
		if isinstance(obj, EmailAddress):
			return obj in self.moderator_emails.all()
		elif isinstance(obj, User):
			return obj in self.moderator_users.all()
		elif isinstance(obj, Group):
			return obj in self.moderator_groups.all()
		else:
			raise TypeError(u"Invalid moderator: %s" % unicode(obj))

	def is_implicit_moderator(self, email):
		if isinstance(obj, EmailAddress):
			return obj.user and (self.is_moderator(obj.user) or self.is_implicit_moderator(obj.user))
		elif isinstance(obj, User):
			return bool(self.moderator_groups.filter(users=obj))
		elif isinstance(obj, Group):
			raise TypeError(u"Groups cannot be implicit moderators.")
		else:
			raise TypeError(u"Invalid moderator: %s" % unicode(obj))

	def can_post(self, obj)
		if self.who_can_post == 'all':
			return True
		
		if self.who_can_post == 'sub' and (self.is_subscriber(obj) or self.is_implicit_subscriber(obj)):
			return True
		
		if self.is_moderator(obj) or self.is_implicit_moderator(obj):
			return True
		
		return False