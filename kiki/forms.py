from django import forms
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db.models import Q

from kiki.models import MailingList, ListUserMetadata


SUBSCRIPTION_USER_PASSWORD = '!KIKI!'


class HoneypotForm(forms.Form):
	honeypot = forms.CharField(help_text="If you enter anything in this field, your subscription will be treated as spam.", required=False)
	
	def clean_honeypot(self):
		value = self.cleaned_data['honeypot']
		
		if value:
			raise ValidationError("The honeypot field must be blank!")
		
		return value


class SubscriptionForm(HoneypotForm):
	email = forms.EmailField()
	
	def __init__(self, *args, **kwargs):
		super(SubscriptionForm, self).__init__(*args, **kwargs)
		self.fields['mailing_list'] = forms.models.ModelChoiceField(MailingList.objects.filter(self_subscribe_enabled=True, domain=Site.objects.get_current()))
	
	def clean_email(self):
		email = self.cleaned_data['email']
		try:
			user = User.objects.get(Q(email__iexact=email) | Q(username__iexact=email))
		except User.DoesNotExist:
			user = User(username=email, password=SUBSCRIPTION_USER_PASSWORD, email=email, is_active=False)
		return user
	
	def clean(self):
		cleaned_data = super(SubscriptionForm, self).clean()
		user = cleaned_data['user']
		mailing_list = cleaned_data['mailing_list']
		self._metadata_cache = None
		if user.pk is not None:
			try:
				self._metadata_cache = ListUserMetadata.objects.get(user=user, mailing_list=mailing_list)
			except ListUserMetadata.DoesNotExist:
				pass
			else:
				# TODO:: Should the validation error be more generic? Is this a
				# security issue?
				if self._metadata_cache.status == ListUserMetadata.BLACKLISTED:
					raise ValidationError("Sorry, but that email has been blacklisted for the selected list.")
				if self._metadata_cache.status != ListUserMetadata.UNCONFIRMED:
					raise ValidationError("That email is already subscribed to the selected list.")
		return cleaned_data
	
	def save(self):
		"""
		Ensures that the :class:`User` exists and that a :class:`.ListUserMetadata` instance exists linking it to the correct :class:`.MailingList`, and returns a (mailing_list, user, metadata) tuple.
		
		"""
		mailing_list = self.cleaned_data['mailing_list']
		user = self.cleaned_data['email']
		
		if user.pk is None:
			user.save()
		
		if self._metadata_cache is None:
			self._metadata_cache = ListUserMetadata.objects.create(user=user, mailing_list=mailing_list)
		return mailing_list, user, self._metadata_cache