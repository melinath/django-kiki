from django import template

from kiki.utils.commands import build_command_address


register = template.Library()


@register.filter
def list_command(mailing_list, command):
	"""Returns the address for accessing the given list command, if such a command exists. Otherwise returns an empty string."""
	try:
		return build_command_address(mailing_list, command)
	except ValueError:
		return ''
