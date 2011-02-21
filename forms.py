from django import forms
from django.core.exceptions import ValidationError
from kiki.models import UserEmail, MailingList
from kiki.fields import MailingListMultipleChoiceField
from django.core.mail import send_mail
from django.contrib.sites.models import Site


class HoneypotForm(forms.Form):
	honeypot = forms.CharField(help_text="If you enter anything in this field, your subscription will be treated as spam.")
	
	def clean_honeypot(self):
		value = self.cleaned_data['honeypot']
		
		if value:
			raise ValidationError("The honeypot field must be blank!")
		
		return value


class EasySubscriptionForm(HoneypotForm):
	mailing_lists = MailingListMultipleChoiceField(MailingList.objects.filter(self_subscribe_enabled=True))
	email = forms.EmailField()
	
	def save(self):
		# Send a confirmation email to the address for each mailing list.
		mailing_lists = self.cleaned_data['mailing_lists']
		if len(mailing_lists) == 1:
			mailing_list = mailing_lists[0]
			send_mail("Confirm subscription", """You've asked to be subscribed to %s.
If this is correct, please send an email to %s-subscribe@%s to confirm your subscription.
If you feel you've received this email in error, please contact %s.""" %
(mailing_list.name, mailing_list.address, mailing_list.site.domain, "the webmaster"),
'noreply@%s' % mailing_list.site.domain, [self.cleaned_data['email']])
		else:
			addresses = "\n".join([
				"%s-subscribe@%s\n" % (mailing_list.address, mailing_list.site.domain)
				for mailing_list in mailing_lists
			])
			list_names = ', '.join([mailing_list.name for mailing_list in mailing_lists])
			send_mail("Confirm subscriptions", """You've asked to be subscribed to
%s. If this is correct, please email the following addresses to confirm your subscriptions:
%s
If you feel you've received this email in error, please contact %s.""" %
(list_names, addresses, "the webmaster"),
"noreply@%s" % Site.objects.get_current().domain, [self.cleaned_data['email']])


class ManageSubscriptionsForm(forms.Form):
	mailing_lists = MailingListMultipleChoiceField(MailingList.objects.filter(self_subscribe_enabled=True), required=False)
	
	def __init__(self, user, *args, **kwargs):
		self.user = user
		super(ManageSubscriptionsForm, self).__init__(*args, **kwargs)
		f = self.fields['mailing_lists']
		f.queryset = f.queryset.exclude(
			subscribed_groups__user = user
		).exclude(
			subscribed_officer_positions__users = user
		).exclude(
			moderator_users = user
		).exclude(
			moderator_groups__user = user
		).exclude(
			moderator_officer_positions__users = user
		).exclude(
			moderator_emails__user = user
		)
		self.initial.update({
			'mailing_lists': f.queryset.filter(subscribed_users=user).values_list('pk', flat=True)
		})
	
	def save(self):
		for mailing_list in self.fields['mailing_lists'].queryset:
			if mailing_list in self.cleaned_data['mailing_lists']:
				mailing_list.subscribe(self.user)
			else:
				mailing_list.unsubscribe(self.user)