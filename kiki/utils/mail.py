from django.core.mail import send_mail
from django.template.defaultfilters import striptags
from django.template.loader import render_to_string


def html_to_plain(html_body):
	return striptags(html_body)
