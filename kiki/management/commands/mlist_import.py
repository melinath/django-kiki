from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from stepping_out.mail.models import MailingList
from django.contrib.sites.models import Site
from optparse import make_option
from sys import stdin
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from cStringIO import StringIO
from stepping_out.mail.utils import add_emails_to_list


class Command(BaseCommand):
	help = 'Imports a file (or stdin) into a mailing list'
	args = '[-s <separator>] <listaddress> [<filename>]'
	
	option_list = BaseCommand.option_list + (
		make_option('-s', '--separator', dest='separator', default=',',
			help='Character(s) separating the email addresses. Default:","'),
	)
	
	def handle(self, *args, **options):
		if not args:
			raise CommandError('At least one argument must be given')
		
		email = args[0].partition('@')
		
		if email[1] == '':
			try:
				mlist = MailingList.objects.get(address=email[0])
			except MailingList.DoesNotExist:
				raise CommandError('No mailing list with address "%s" exists' % email[0])
			except MailingList.MultipleObjectsReturned:
				raise CommandError('Multiple lists begin with "%s". Please specify a full address.' % email[0])
		elif email[1] == '@' and len(email[2]) > 0:
			try:
				mlist = MailingList.objects.get(address=email[0], site__domain=email[2])
			except MailingList.DoesNotExist:
				mlist = MailingList(address=email[0])
				mlist.save()
				mlist.site, created = Site.objects.get_or_create(domain=email[2])
		else:
			raise CommandError('"%s" is not a valid email address.' % args[0])
		
		if len(args) == 1:
			fp = StringIO()
			fp.write(stdin.read())
			fp.seek(0)
			self.stdout.write('\n\n')
		elif len(args) == 2:
			fp = open(args[1], 'r')
		else:
			raise CommandError('Too many arguments')
		
		emails = set()
		
		for line in fp:
			emails |= set([email.strip() for email in line.split(options['separator'])])
		
		errors = add_emails_to_list(mlist, emails)
		
		if options['verbosity'] > 0:
			if errors:
				for e in errors:
					self.stdout.write(e)
		
		if not errors:
			self.stdout.write("Emails imported successfully.\n\n")