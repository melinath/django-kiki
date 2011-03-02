from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
from django.db.models import Q, F
from django.utils import simplejson as json
from django.utils.encoding import smart_str

from email import message_from_string
from email.utils import getaddresses

from kiki.commands import is_command
from kiki.message import Message as KikiMessage
from kiki.validators import validate_local_part, validate_not_command
from kiki.utils import precook_headers, cook_headers, send_mail
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
	subject_prefix = models.CharField(max_length=10, blank=True)
	local_part = models.CharField(max_length=64, validators=[validate_local_part, validate_not_command])
	domain = models.ForeignKey(Site)
	description = models.TextField(blank=True)
	
	who_can_post = models.CharField(max_length=3, choices=SUBSCRIPTION_CHOICES)
	self_subscribe_enabled = models.BooleanField(verbose_name = 'self-subscribe enabled')
	# If is_anonymous becomes an option, the precooker will need to handle some anonymizing.
	#is_anonymous = models.BooleanField()
	
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
	
	@property
	def list_id_header(self):
		# Does this need to be a byte string?
		return smart_str(u"%s <%s.%s>" % (self.name, self.local_part, self.site.domain))
	
	def __unicode__(self):
		return self.name
	
	def clean(self):
		validate_email(self.address)
		
		# As per RFC 2919, the list_id_header has a max length of 255 octets.
		if len(self.list_id_header) > 254:
			# Allow 4 extra spaces: the delimiters, the space, and the period.
			raise ValidationError("The list name, local part, and site domain name can be at most 250 characters long.")
	
	def get_recipients(self):
		q = Q(subscribed_mailinglist_set=self) | Q(moderated_mailinglist_set=self)
		q |= Q(user__subscribed_mailinglist_set=self, user__email=F('email')) | Q(user__moderated_mailinglist_set=self, user__email=F('email'))
		q |= Q(user__groups__subscribed_mailinglist_set=self) | Q(user__groups__moderated_mailinglist_set=self)
		
		return EmailAddress.objects.filter(q).values_list('email', flat=True).distinct()
	
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


class ProcessingAttempt(models.Model):
	UNPROCESSED = "u"
	ERROR = "e"
	REJECTED = "r"
	PROCESSED = "p"
	
	STATUS_CHOICES = (
		(UNPROCESSED, "Unprocessed"),
		(ERROR, "Error"),
		(REJECTED, "Rejected"),
		(PROCESSED, "Processed"),
	)
	status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=UNPROCESSED, db_index=True)
	
	error = models.TextField(blank=True, help_text="This field will be filled with error data if any problems occur during message processing.")
	
	mailing_list = models.ForeignKey(MailingList)
	message = models.ForeignKey(Message, related_name="processing_attempts")
	timestamp = models.DateTimeField(auto_now_add=True)
	
	def process(self, connection=None):#, retry=False):
		"""
		Try to process the message, and return a ProcessingAttempt,
		either self or a new attempt. TODO: Should this just always return a
		new instance?
		"""
		if self.status == self.PROCESSED:
			# We've done this already. Return self.
			return self
		elif self.status != self.UNPROCESSED:
			# Make a new ProcessingAttempt and return the results of its processing.
			attempt = ProcessingAttempt(mailing_list=self.mailing_list, message=self.message)
			return attempt.process(connection)
		else:
			# Process! Woot!
			# 1. unpickle
			# 2. cook the message headers.
			# 3. gather recipients for the list.
			# 4. send the message.
			msg = cPickle.loads(self.message.message)
			cook_headers(msg, self.mailing_list)
			
			recipients = self.mailing_list.get_recipients()
			send_mail(msg, recipients, connection)
	
	class Meta:
		get_latest_by = 'timestamp'


class MessageManager(models.Model):
	def receive(self, text):
		"Returns a created Message instance or None."
		msg = message_from_string(text, KikiMessage)
		
		# Check whether the message should even be received.
		# First collect a set of addresses.
		headers = ['to', 'cc', 'resent-to', 'resent-cc']
		addresses = set()
		address_commands = {}
		forwards = set()
		for header in headers:
			# Discard the name portion of each address and split it into local_part, domain_name tuples.
			for address in getaddresses(msg.get_all(header, [])):
				local_part, domain_name = address[1].rsplit('@', 1)
				local_part, command = local_part.rsplit('-', 1)
				
				if is_command(command):
					address_commands.setdefault((local_part, domain_name), []).append(command)
				else:
					local_part = '-'.join(local_part, command)
					forwards.add((local_part, domain_name))
				
				addresses.add((local_part, domain_name))
		
		if not addresses:
			return None
		
		mailing_lists = MailingList.objects.for_addresses(addresses)
		
		if not mailing_lists:
			return None
		
		# TODO: Handle commands here! I.e. if something only has a subscribe command,
		# we should just run it without saving the email to the db.... or should we?
		# DB Logging?
		
		# Set some headers that need to be there, and remove some others.
		precook_headers(msg)
		
		message = Message(message_id=msg['message-id'], received_at=datetime.datetime.now())
		message.message = cPickle.dumps(msg, cPickle.HIGHEST_PROTOCOL)
		message.save()
		
		for mailing_list in mailing_lists:
			attempt = ProcessingAttempt(mailing_list=mailing_list, message=message)
			attempt.process()
		
		return message


class Message(models.Model):
	objects = MessageManager()
	
	mailing_lists = models.ManyToManyField(MailingList, through=Processing)
	message_id = models.CharField(max_length=255, unique=True)
	received = models.DateTimeField()
	
	# This should be a custom field & descriptor to handle cached message parsing.
	# Or perhaps a PickleField?
	message = models.TextField(help_text="The original raw text of the message (pickled).")
	
	@property
	def processed(self):
		return bool(self.processing_attempts.filter(status=ProcessingAttempt.PROCESSED))