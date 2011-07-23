from django import forms
from django.core.exceptions import ValidationError
from kiki.models import EmailAddress, MailingList
from kiki.fields import MailingListMultipleChoiceField
from django.contrib.sites.models import Site


class HoneypotForm(forms.Form):
	honeypot = forms.CharField(help_text="If you enter anything in this field, your subscription will be treated as spam.", required=False)
	
	def clean_honeypot(self):
		value = self.cleaned_data['honeypot']
		
		if value:
			raise ValidationError("The honeypot field must be blank!")
		
		return value


class SubscriptionForm(HoneypotForm):
	mailing_list = forms.models.ModelChoiceField(MailingList.objects.filter(self_subscribe_enabled=True))
	email = forms.EmailField()
	
	template = "kiki/notifications/subscription_confirm.eml"
	
	def clean_email(self):
		email = self.cleaned_data['email']
		try:
			email = EmailAddress.objects.get(email__iexact=email)
		except EmailAddress.DoesNotExist:
			email = EmailAddress(email=email)
		return email
	
	def save(self):
		# Send a confirmation email to the address for the selected mailing list.
		mailing_list = self.cleaned_data['mailing_list']
		email = self.cleaned_data['email']
		
		if email.pk is None:
			email.save()
		
		send_confirmation_email(mailing_list, email, self.template)