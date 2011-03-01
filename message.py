from django.utils.encoding import force_unicode
from email.message import Message as DefaultMessage


class Message(DefaultMessage):
	def __getitem__(self, key):
		value = super(Message, self).__getitem__(key)
		return force_unicode(value)
	
	def get(self, key, failobj=None):
		value = super(Message, self).get(key, failobj)
		return force_unicode(value)
	
	def get_all(self, key, failobj=None):
		all_values = super(Message, self).get_all(key, failobj)
		try:
			return [force_unicode(value) for value in all_values]
		except:
			return failobj
	
	@property
	def sender(self):
		for h in ('from', 'from_', 'Reply-To', 'Sender'):
			if h == 'from_':
				hval = self.get_unixfrom()
			else:
				hval = self[h]
			if not hval:
				continue
			
			addrs = getaddresses([hval])
			try:
				realname, address = addrs[0]
				return address
			except IndexError:
				continue
		return ''


#from email.header import Header
#from email.message import Message
#from email.utils import getaddresses, parseaddr
#from django.conf import settings
#from django.utils.functional import curry
#from kiki.commands import run_command, COMMANDS
#from kiki.logs import LOGGER
#from kiki.models import MailingList
#import logging
#import re
#
#
#CONTINUATION_WS = '\t'
#CONTINUATION = ',\n' + CONTINUATION_WS
#COMMASPACE = ', '
#MAXLINELEN = 78
#
#
#nonascii = re.compile('[^\s!-~]')
#
#
#def get_encoded_header(s):
#	# I'm going to be a little more us-ascii-centric... right now, you can't set
#	# the default charset for a list anyway, and I don't anticipate this being
#	# that large of a project...
#	charset = 'us-ascii'
#	if nonascii.search(s):
#		charset = 'iso-8859-1'
#	return Header(s, charset)
#
#
#class SteppingOutMessage(Message):
#	"""
#	This subclasses the default python email class. It contains a function to
#	generate metadata based on its own contents to prepare it for shipping.
#	Important! It doesn't ACT on the metadata. It only creates it.
#	"""
#	def __init__(self, *args, **kwargs):
#		Message.__init__(self, *args, **kwargs)
#		self._addresses_parsed = False
#		self._sender_parsed = False
#		
#		self.original_sender = ''
#		self.recipient_emails = set()
#		
#		self.commands = set() # This will be a set of curried functions
#		self.skip_addresses = set() # These addresses will already be receiving the email and shouldn't get a copy.
#		self.mailing_lists = set() # This will be a set of MailingLists that are targeted to receive an email
#		self.missing_addresses = set() # This is a set of email addresses at the current domain which can't be matched to lists
#	
#	@property
#	def log(self):
#		if not hasattr(self, '_log'):
#			self._log = logging.LoggerAdapter(
#				LOGGER,
#				{'msgid': self.id}
#			)
#		
#		return self._log
#	
#	@property
#	def id(self):
#		return str(self['Message-ID'])
#	
#	@property
#	def sender(self):
#		for h in ('from', 'from_', 'Reply-To', 'Sender'):
#			if h == 'from_':
#				hval = self.get_unixfrom()
#			else:
#				hval = self[h]
#			if not hval:
#				continue
#			
#			addrs = getaddresses([hval])
#			try:
#				realname, address = addrs[0]
#				return address
#			except IndexError:
#				continue
#		return ''
#	
#	def __getitem__(self, key):
#		# Ensure that header values are unicodes.
#		value = Message.__getitem__(self, key)
#		if isinstance(value, str):
#			return unicode(value, 'ascii')
#		return value
#	
#	def get(self, name, failobj=None):
#		# Ensure that header values are unicodes.
#		value = Message.get(self, name, failobj)
#		if isinstance(value, str):
#			return unicode(value, 'ascii')
#		return value
#	
#	def get_addr_set(self, arg):
#		# return just the email address; drop the realname. Will patch in from
#		# User object later.
#		addresses = getaddresses(self.get_all(arg, []))
#		return set([address[1] for address in addresses])
#	
#	def parse_addrs(self):
#		self.get_sender_addr()
#		self.parse_to_and_cc()
#	
#	def get_sender_addr(self):
#		if not self._sender_parsed:
#			self.original_sender = parseaddr(self.sender)[1]
#			self._sender_parsed = True
#	
#	def parse_to_and_cc(self):
#		"""
#		Check the original to and cc addresses to see if this message was even
#		sent to a list. Split the addresses into:
#			1. things to omit.
#			2. things that are lists.
#			3. things that are automated list functions
#			4. things that fail to find a target.
#	
#		TODO: What about multiline address lists? Do I need to worry about unwrapping?
#		Mailman comments claim a getaddresses bug...
#		"""
#		if self._addresses_parsed:
#			#Then we were already here.
#			return
#		
#		headers = ['to', 'cc', 'resent-to', 'resent-cc']
#		mailing_lists = MailingList.objects.by_domain()
#		
#		for header in headers:
#			addresses = self.get_addr_set(header)
#			for address in addresses:
#				if address in OUR_ADDRESSES:
#					continue
#				
#				name, domain = address.split('@')
#				
#				if domain not in mailing_lists:
#					# Then ignore it - they're getting the message elsehow.
#					self.skip_addresses.add(address)
#					continue
#				
#				if name in mailing_lists[domain]:
#					# Then plan to send the email to this list
#					self.mailing_lists.add(mailing_lists[domain][name])
#					continue
#				elif '-' in name:
#					# Could be a command?
#					name, command = name.rsplit('-', 1)
#					
#					if command and command in COMMANDS and name in mailing_lists[domain]:
#						self.commands.add(curry(run_command, mailing_list=mailing_lists[domain][name], command=command))
#						continue
#				
#				self.missing_addresses.add(address)
#		
#		self._addresses_parsed = True
#	
#	def cook_headers(self):
#		"""
#		Remove: DKIM
#		"""
#		list_addrs = set([mailing_list.full_address for mailing_list in self.mailing_lists])
#		for addr in list_addrs:
#			self['X-BeenThere'] = addr
#		
#		if 'precedence' not in self:
#			self['Precedence'] = 'list'
#		
#		# Reply-To should be whatever it was plus whatever lists this is being sent to.
#		reply_to = set([address[1] for address in getaddresses(self.get_all('reply-to', []))]) | list_addrs
#		del self['reply-to']
#		if reply_to:
#			self['Reply-To'] = COMMASPACE.join(reply_to)
#		
#		# To and Cc should be able to stay the same... though we can also put things back
#		# right if necessary.
#		# The whole 'letting people send messages to multiple lists' thing is getting to me.
#		# It causes problems. Like how do I set the list headers if it's going to
#		# three different lists?
#		
#		# Delete DKIM headers since they will not refer to our message.
#		del self['domainkey-signature']
#		del self['dkim-signature']
#		del self['authentication-results']