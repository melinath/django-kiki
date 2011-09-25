from django.core.mail.message import EmailMessage


def create_test_email(from_email, to, subject='hello', body='This is clearly a test.', headers=None):
	"""
	Returns a string representation of an email message.
	
	"""
	headers = headers or {}
	msg = EmailMessage(subject, body, from_email, to, headers=headers)
	msg_str = msg.message().as_string()
	return msg_str
