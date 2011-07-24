import base64
import cPickle as pickle
import datetime
from email import message_from_string
from email.utils import getaddresses


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


from kiki.commands import is_command
from kiki.message import Message as KikiMessage
from kiki.validators import validate_local_part, validate_not_command
from kiki.utils import precook_headers, cook_headers, send_mail


class ListUserMetadata(models.Model):
	UNCONFIRMED = 0
	SUBSCRIBER = 1
	MODERATOR = 2
	BLACKLISTED = 3
	
	STATUS_CHOICES = (
		(UNCONFIRMED, u'Unconfirmed'),
		(SUBSCRIBER, u'Subscriber'),
		(MODERATOR, u'Moderator'),
		(BLACKLISTED, u'Blacklisted'),
	)
	
	user = models.ForeignKey(User)
	mailing_list = models.ForeignKey('MailingList')
	
	status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=UNCONFIRMED, db_index=True)
	
	def __unicode__(self):
		return u"%s - %s - %s" % (self.email, self.mailing_list, self.get_status_display())
	
	class Meta:
		unique_together = ('email', 'mailing_list')


class MailingListManager(models.Manager):
	def for_site(self, site):
		return self.filter(site=site)
	
	def for_addresses(self, addresses):
		"""
		Takes a an iterable of email addresses and returns a queryset of mailinglists attached to the current site with matching local parts.
		
		"""
		site = Site.objects.get_current()
		
		local_parts = []
		
		for addr in addresses:
			addr = addr.rsplit('@', 1)
			if addr[1] == site.domain_name:
				local_parts.append(addr[0])
		
		if not local_parts:
			return self.none()
		
		return self.filter(site=site, local_part__in=local_parts)


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
	self_subscribe_enabled = models.BooleanField(verbose_name='self-subscribe enabled')
	moderation_enabled = models.BooleanField(help_text="If enabled, messages will be marked ``Requires Moderation`` and an email will be sent to the list's moderators.")
	# If is_anonymous becomes an option, the precooker will need to handle some anonymizing.
	#is_anonymous = models.BooleanField()
	
	users = models.ManyToManyField(
		User,
		related_name = 'mailinglists',
		blank = True,
		null = True,
		through = ListUserMetadata
	)
	messages = models.ManyToManyField(
		'Message',
		related_name = 'mailinglists',
		blank = True,
		null = True,
		through = 'ListMessage'
	)
	
	@property
	def address(self):
		return "%s@%s" % (self.local_part, self.domain.domain)
	
	def _command_header(self, command_str=None):
		if command_str:
			addr = "%s+%s@%s" % (self.local_part, command_str, self.domain.domain)
		else:
			addr = self.address
		return "<mailto:%s>" % addr
	
	def _list_id_header(self):
		# Does this need to be a byte string?
		return smart_str(u"%s <%s.%s>" % (self.name, self.local_part, self.domain.domain))
	
	def __unicode__(self):
		return self.name
	
	def clean(self):
		validate_email(self.address)
		
		# As per RFC 2919, the list_id_header has a max length of 255 octets.
		if len(self.list_id_header) > 254:
			# Allow 4 extra spaces: the delimiters, the space, and the period.
			raise ValidationError("The list name, local part, and site domain name can be at most 250 characters long together.")
	
	def get_recipients(self):
		"""Returns a queryset of :class:`User`\ s that should receive this message."""
		qs = User.objects.filter(is_active=True)
		qs = qs.filter(listusermetadata_set__mailing_list=self, listusermedatata_set__status__in=[ListUserMetadata.SUBSCRIBER, ListUserMetadata.MODERATOR])
		return qs.distinct()
	
	def _is_email_with_status(self, email, status):
		if isinstance(email, basestring):
			kwargs = {'user__email__iexact': email}
		elif isinstance(email, User):
			kwargs = {'user': email}
		else:
			return False
		
		try:
			self.listusermetadata_set.get(status=status, **kwargs)
		except ListUserMetadata.DoesNotExist:
			return False
		return True
	
	def is_subscriber(self, email):
		return self._is_email_with_status(email, ListUserMetadata.SUBCRIBER)
	
	def is_moderator(self, email):
		return self._is_email_with_status(email, ListUserMetadata.MODERATOR)
	
	def can_post(self, email):
		if self.who_can_post == MailingList.ANYONE:
			return True
		
		if self.who_can_post == MailingList.SUBSCRIBERS and self.is_subscriber(email):
			return True
		
		if self.is_moderator(email):
			return True
		
		return False


class ProcessedMessageModel(models.Model):
	"""
	Encapsulates the logic required for storing and fetching pickled EmailMessage objects. This should eventually be replaced with a custom model field.
	
	"""
	processed_message = models.TextField(help_text="The processed form of the message at the current stage (pickled).", blank=True)
	
	# Store the message as a base64-encoded pickle dump a la django-mailer.
	def set_processed(self, msg):
		self.processed_message = base64.encodestring(pickle.dumps(msg, pickle.HIGHEST_PROTOCOL))
		self._processed = msg
	
	def get_processed(self):
		if not hasattr(self, '_processed'):
			self._processed = pickle.loads(base64.decodestring(self.processed_message))
		return self._processed
	
	class Meta:
		abstract = True


class Message(ProcessedMessageModel):
	"""
	Represents an email received by Kiki. Stores the original received message as well as a pickled version of the processed message.
	
	"""
	RECEIVED = 1
	ATTACHED = 2
	COMMANDS = 3
	ATT_COMM = 4
	
	STATUS_CHOICES = (
		(RECEIVED, 'Received'),
		(ATTACHED, 'Attached to mailing lists'),
		(COMMANDS, 'Commands run'),
		(ATT_COMM, 'Attached to mailing lists and commands run')
	)
	
	message_id = models.CharField(max_length=255, unique=True)
	#: The message_id of the email this is in reply to.
	# in_reply_to = models.CharField(max_length=255, db_index=True, blank=True)
	from_email = models.EmailField()
	
	received = models.DateTimeField()
	
	status = models.PositiveIntegerField(choices=STATUS_CHOICES, db_index=True, default=RECEIVED)
	
	original_message = models.TextField(help_text="The original raw text of the message.")


class ListMessage(ProcessedMessageModel):
	"""
	Represents the relationship between a :class:`Message` and a :class:`MailingList`. This is what is processed to handle the sending of a message to a list rather than the original message.
	
	"""
	UNPROCESSED = 1
	REQUIRES_MODERATION = 2
	REJECTED = 3
	ACCEPTED = 4
	PREPPED = 5
	SENT = 6
	FAILED = 7
	
	STATUS_CHOICES = (
		(UNPROCESSED, 'Unprocessed'),
		(REQUIRES_MODERATION, 'Requires Moderation'),
		(REJECTED, 'Rejected'),
		(ACCEPTED, 'Accepted'),
		(PREPPED, 'Prepped'),
		(SENT, 'Sent'),
		(FAILED, 'Failed'),
	)
	
	message = models.ForeignKey(Message)
	mailing_list = models.ForeignKey(MailingList)
	status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, db_index=True, default=UNPROCESSED)
	
	class Meta:
		unique_together = ('message', 'mailing_list',)


class ListCommand(models.Model):
	UNPROCESSED = 1
	REJECTED = 2
	ACCEPTED = 3
	COMPLETED = 4
	
	STATUS_CHOICES = (
		(UNPROCESSED, 'Unprocessed'),
		(REJECTED, 'Rejected'),
		(ACCEPTED, 'Accepted'),
		(COMPLETED, 'Completed'),
	)
	
	message = models.ForeignKey(Message)
	mailing_list = models.ForeignKey(MailingList)
	status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, db_index=True, default=UNPROCESSED)
	
	command = models.CharField(max_length=20)