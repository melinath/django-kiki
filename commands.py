"""
This file defines an interface with all list commands from RFC 2369, along with
functions to access the commands, generate List- headers, etc. Any commands
which are not yet supported will raise a NotImplementedError if they
are accessed.
"""


class ListCommand(object):
	def get_address(self, mailing_list):
		"Return the address associated with this command."
		raise NotImplementedError
	
	def set_list_header(self, msg, mailing_list):
		"Set this header on the msg, replacing any pre-existing headers of the same name."
		raise NotImplementedError


COMMANDS = {
	'help': ListCommand,
	'unsubscribe': ListCommand,
	'subscribe': ListCommand,
	'post': ListCommand,
	'owner': ListCommand,
	'archive': ListCommand,
	
	# This is the odd one out... no header for it. Just returns "information on how to administer subscriptions"
	# See http://www.jamesshuggins.com/h/web1/list-email-headers.htm
	'request': ListCommand,
	
	# ...and a private one to quiet all complaints.
	'bounce': ListCommand
}
COMMAND_KEYS = COMMANDS.keys()


def is_command(command):
	return command in COMMAND_KEYS


def get_command(command):
	"Return an instance of the stored command or an anonymous command."
	return COMMANDS.get(command, ListCommand)()


def add_list_command_headers(msg, mailing_list, commands=COMMAND_KEYS):
	"""For each command, try to fetch it and run its add_list_header method.
	Modifies the msg in place."""
	for command in commands:
		try:
			get_command(command).set_list_header(msg, mailing_list)
		except NotImplementedError:
			pass


def get_command_addresses(mailing_list, commands=COMMAND_KEYS):
	"""For each command, try to fetch it and run its get_address method.
	Returns a list of addresses."""
	addresses = []
	for command in commands:
		try:
			addresses.append(get_command(command).get_address(mailing_list))
		except NotImplementedError:
			pass
	return addresses


from django.core.mail import send_mail


def subscribe(email, mailing_list):
	mailing_list.subscribe(email)
	send_mail("Subscription successful", """You've been subscribed to %s! You can
unsubscribe at any time by sending an email to %s-unsubscribe@%s""" %
(mailing_list.name, mailing_list.address, mailing_list.site.domain),
"noreply@%s" % mailing_list.site.domain, [email])


def unsubscribe(email, mailing_list):
	mailing_list.unsubscribe(email)
	send_mail("Unsubscription successful", """You've been unsubscribed from %s. You can
resubscribe at any time by sending an email to %s-subscribe@%s""" %
(mailing_list.name, mailing_list.address, mailing_list.site.domain),
"noreply@%s" % mailing_list.site.domain, [email])


def bounce(email, mailing_list):
	pass


COMMANDS = {
	'subscribe': subscribe,
	'bounce': bounce,
	'unsubscribe': unsubscribe,
}


def run_command(command, email, mailing_list):
	COMMANDS[command](email, mailing_list)