from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.utils.http import base36_to_int, int_to_base36
from django.views.generic import View, FormView

from kiki.forms import SubscriptionForm
from kiki.models import ListUserMetadata
from kiki.utils.commands import build_command_address
from kiki.utils.mail import html_to_plain
from kiki.utils.subscription import token_generator as subscription_token_generator


class EmailViewMixin(object):
	subject_template_name = None
	body_template_name = None
	use_https = False
	use_html = True
	email_message_class = EmailMultiAlternatives
	success_message = None
	
	def get_success_message(self):
		return self.success_message
	
	def get_email_context(self):
		site = self.mailing_list.domain
		site_name = site.name
		domain = site.domain
		return {
			'domain': domain,
			'site_name': site_name,
			'protocol': 'https' if self.use_https else 'http'
		}
	
	def get_from_email(self):
		return settings.DEFAULT_FROM_EMAIL
	
	def get_to_addresses(self):
		return []
	
	def get_subject(self):
		subject = render_to_string(self.subject_template_name, self.email_context)
		# Enforce single-line subject
		return ''.join(subject.splitlines())
	
	def get_body(self):
		return render_to_string(self.body_template_name, self.email_context)
	
	def build_message(self):
		"""
		Returns an :class:`EmailMultiAlternatives` instance.
		
		"""
		self.email_context = self.get_email_context()
		subject = self.get_subject()
		html_body = self.get_body()
		from_email = self.get_from_email()
		to = self.get_to_addresses()
		plain_body = html_to_plain(html_body)
		msg = self.email_message_class(subject, body, from_email, to)
		if self.use_html:
			msg.attach_alternative(html_body, "text/html")
		return msg
	
	def send_email(self):
		msg = self.build_email()
		msg.send()
		messages.add_message(self.request, messages.INFO, self.get_success_message())


class SubscriptionView(EmailViewMixin, FormView):
	template_name = "kiki/subscription.html"
	subject_template_name = 'kiki/email/subscription/confirmation_subject.txt'
	body_template_name = 'kiki/email/subscription/confirmation_body.html'
	token_generator = subscription_token_generator
	form_class = SubscriptionForm
	success_url = ''
	
	def form_valid(self, form):
		self.mailing_list, self.user, self.metadata = form.save()
		self.send_email()
		return super(SubscriptionView, self).form_valid()
	
	def get_email_context(self):
		context = super(SubscriptionView, self).get_email_context()
		context.update({
			'email': self.user.email,
			'mid': int_to_base36(self.metadata.pk),
			'metadata': self.metadata,
			'user': self.user,
			'mailing_list': self.mailing_list,
			'token': self.token_generator.make_token(self.metadata)
		})
		return context
	
	def get_from_email(self):
		return build_command_address(self.mailing_list, 'bounce')
	
	def get_to_addresses(self):
		return [self.user.email]


class SubscriptionConfirmationView(EmailViewMixin, View):
	token_generator = subscription_token_generator
	success_url = '/'
	subject_template_name = 'kiki/email/subscription/confirmed_subject.txt'
	body_template_name = 'kiki/email/subscription/confirmed_body.html'
	
	def get_success_url(self):
		return self.success_url
	
	def confirm_subscriber(self):
		self.metadata.status = ListUserMetadata.SUBSCRIBER
		self.metadata.save()
	
	def get_from_email(self):
		return build_command_address(self.metadata.mailing_list, 'bounce')
	
	def get_to_addresses(self):
		return [self.metadata.user.email]
	
	def get_email_context(self):
		context = super(SubscriptionConfirmationView, self).get_email_context(self)
		context.update({
			'email': self.metadata.user.email,
			'metadata': self.metadata,
			'user': self.metadata.user,
			'mailing_list': self.mailing_list
		})
		return context
	
	def get_metadata(self):
		try:
			mid_int = base36_to_int(self.kwargs['midb36'])
			return ListUserMetadata.objects.select_related('user', 'mailing_list').get(pk=mid_int)
		except (ValueError, KeyError, ListUserMetadata.DoesNotExist):
			return None
	
	def get(self, request, *args, **kwargs):
		self.metadata = self.get_metadata()
		token = self.kwargs.get('token', None)
		
		if self.metadata is not None and token is not None and self.token_generator.check_token(self.metadata, token):
			self.confirm_subscriber()
			self.send_email()
			return HttpResponseRedirect(self.get_success_url())
		raise Http404