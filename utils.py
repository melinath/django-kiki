from kiki.models import MailingList, UserEmail
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


def add_emails_to_list(mailing_list, emails):
	errors = []
	for email in emails:
		try:
			mailing_list.subscribe(email)
		except ValidationError, e:
			errors.append(e)
			continue
	
	#mailing_list.save()
	
	return errors