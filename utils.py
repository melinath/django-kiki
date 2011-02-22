from django.core.exceptions import ValidationError


def add_emails_to_list(mailing_list, emails):
	errors = []
	for email in emails:
		try:
			mailing_list.subscribe(email)
		except ValidationError, e:
			errors.append(e)
			continue
	
	return errors