from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.test import TestCase

from kiki.models import MailingList
from kiki.utils.commands import COMMANDS, build_command_address, parse_command_address
from kiki.utils.mail import html_to_plain


class CommandUtilsTestCase(TestCase):
	def test_build_command_address(self):
		site = Site.objects.create(name="there", domain="there.com")
		mailing_list = MailingList(local_part="hi", domain=site)
		self.assertEqual(build_command_address(mailing_list, "subscribe"), "hi+subscribe@there.com")
		self.assertRaises(ValueError, build_command_address, mailing_list, "raid")
	
	def test_parse_command_address(self):
		for command in COMMANDS:
			actual = parse_command_address("list+%s@test.com" % command)
			expected = ("list", command, "test.com")
			self.assertEqual(actual, expected)
		
		actual = parse_command_address("list+ttt@test.com")
		expected = ("list+ttt", None, "test.com")
		self.assertEqual(actual, expected)
		actual = parse_command_address("list@test.com")
		expected = ("list", None, "test.com")
		self.assertEqual(actual, expected)


class MailUtilsTestCase(TestCase):
	def test_html_to_plain(self):
		test_text = """<p><a href="http://google.com">Google</a> can be useful sometimes.</p>"""
		self.assertEqual(html_to_plain(test_text), "Google can be useful sometimes.")
