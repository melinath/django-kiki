from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import simplejson as json

from email import message_from_string
from email.utils import parseaddr, formatdate, make_msgid, getaddresses

from kiki.message import Message as KikiMessage
from kiki.validators import validate_local_part
import cPickle, datetime


class NoAddressesFound(Exception):
	pass


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


class MailingListManager(models.Manager):
	def for_site(self, site):
		return self.filter(site=site)
	
	def for_addresses(self, addresses):
		"""Takes a an iterable of (local_part, domain_name) tuples and returns
		a queryset of mailinglists attached to the current site with matching
		local parts."""
		site = Site.objects.get_current()
		
		valid_local_parts = [address[0] for address in addresses if address[1] == site.domain_name]
		
		if not valid_local_parts:
			return self.none()
		
		return self.filter(site=site, local_part__in=valid_local_parts)


class MailingList(models.Model):
	"""
	This model contains all options for a mailing list, as well as some helpful
	methods for accessing subscribers, moderators, etc.
	"""
	objects = MailingListManager()
	
	MODERATORS = "mod"
	SUBSCRIBERS = "sub"
	ANYONE = "all"
	
	SUBSCRIPTION_CHOICES = (
		(MODERATORS, 'Moderators',),
		(SUBSCRIBERS, 'Subscribers',),
		(ANYONE, 'Anyone',),
	)
	
	name = models.CharField(max_length=50)
	local_part = models.CharField(max_length=64, validators=[validate_local_part])
	domain = models.ForeignKey(Site)
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
	
	@property
	def address(self):
		return '@'.join((self.local_part, self.domain.domain_name))
	
	def __unicode__(self):
		return self.name
	
	def clean(self):
		validate_email(self.address)
	
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


class Processing(models.Model):
	RECEIVED = "0"
	REJECTED = "1"
	PROCESSED = "2"
	
	# Should there be distinctions of why it was rejected? Perhaps just enter
	# that into the errors field.
	STATUS_CHOICES = (
		(RECEIVED, "Received"),
		(REJECTED, "Rejected"),
		#(ACCEPTED, "Accepted"),
		(PROCESSED, "Processed"),
	)
	status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=RECEIVED)
	error = models.TextField(blank=True, help_text="This field will be filled with error data if any problems occur during message processing.")
	
	mailing_list = models.ForeignKey(MailingList)
	message = models.ForeignKey(Message)
	
	class Meta:
		unique_together = ('mailing_list', 'message')


class MessageManager(models.Model):
	def receive(self, text):
		"Returns a created Message instance or None."
		msg = message_from_string(text, KikiMessage)
		
		# Check whether the message should even be received.
		# First collect a set of addresses.
		headers = ['to', 'cc', 'resent-to', 'resent-cc']
		addresses = set()
		for header in headers:
			# Discard the name portion of each address and split it into local_part, domain_name tuples.
			addresses |= set([tuple(address.rsplit('@', 1)) for address in get_addresses(msg.get_all(header, []))])
		
		if not addresses:
			return None
		
		mailing_lists = MailingList.objects.for_addresses(addresses)
		
		if not mailing_lists:
			return None
		
		# Set some headers that need to be there.
		if 'message-id' not in msg:
			msg['Message-ID'] = make_msgid()
		if 'date' not in msg:
			msg['Date'] = formatdate()
		
		message = Message(message_id=msg['message-id'], received_at=datetime.datetime.now())
		message.message = cPickle.dumps(msg, cPickle.HIGHEST_PROTOCOL)
		message.save()
		
		for mailing_list in mailing_lists:
			Processing.objects.create(
				mailing_list = mailing_list,
				message = message,
				status = Processing.RECEIVED
			)
		
		return message


class Message(models.Model):
	objects = MessageManager()
	
	mailing_lists = models.ManyToManyField(MailingList, through=Processing)
	message_id = models.CharField(max_length=255, unique=True)
	received_at = models.DateTimeField()
	
	# This should be a custom field & descriptor to handle cached message parsing.
	# Or perhaps a PickleField?
	message = models.TextField(help_text="The original raw text of the message (pickled).")