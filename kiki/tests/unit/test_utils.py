from django.contrib.sites.models import Site
from django.test import TestCase

from kiki.models import MailingList
from kiki.utils.commands import COMMANDS, build_command_address, parse_command_address


class CommandUtilsTestCase(TestCase):
	def test_build_command_address(self):
		site = Site.objects.create(name="there", domain="there.com")
		mailing_list = MailingList(local_part="hi", domain=site)
		self.assertEqual(build_command_address(mailing_list, "subscribe"), "hi+subscribe@there.com")
		self.assertRaises(ValueError, build_command_address, (mailing_list, "raid"))
	
	def test_parse_command_address(self):
		for command in COMMANDS:
			actual = parse_command_address("list+%s@test.com" % command)
			expected = ("list", command, "test.com")
			self.assertEqual(actual, expected)
		
		actual = parse_command_address("list+ttt@test.com")
		expected = ("list+ttt", "post", "test.com")
		self.assertEqual(actual, expected)
		actual = parse_command_address("list@test.com")
		expected = ("list", "post", "test.com")
		self.assertEqual(actual, expected)
