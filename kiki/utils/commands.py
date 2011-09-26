COMMANDS = set([
	'post',
	'subscribe',
	'unsubscribe',
	'bounce',
	# "Request" is the odd one out... Just returns
	# "information on how to administer subscriptions"
	# See http://www.jamesshuggins.com/h/web1/list-email-headers.htm
	'request',
])


def build_command_address(mailing_list, command):
	"""
	Given a mailing list and a command, returns the address for the command, using the format ``local+command@domain``. If the command is not recognized, raises a :exc:`ValueError`.
	
	"""
	if command not in COMMANDS:
		raise ValueError(u"Unknown command: %s" % unicode(command))
	return "%s+%s@%s" % (mailing_list.local_part, command, mailing_list.domain.domain)


def parse_command_address(address):
	"""
	Given an address, returns a (local_part, command, address) tuple. Command addresses are expected to be formatted as ``local+command@domain``.
	
	"""
	local, domain = address.rsplit("@", 1)
	command = local.rsplit("+", 1)
	try:
		command = command[1]
	except IndexError:
		command = None
	
	if command:
		if command in COMMANDS:
			local = local[:-(len(command) + 1)]
		else:
			command = None
	
	return local, command, domain
